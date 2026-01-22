class ElementOld:

    def __init__(
        self,
        *,
        bounds: Rect | None = None,
        minimum: Vec2 = Vec2(),
        priority: float = 1.0,
        anchors: Anchors | None = None,
        offsets: Offsets | None = None,
        size: Vec2 | None = None,
        position: Vec2 | None = None,
        uid: UUID | None = None,
    ) -> None:
        self._uid: UUID = uid if uid is not None else uuid4()

        # -- AREA VALUES --

        # The bounds is the area provided by the element's parent
        self._bounds: Rect | None = None
        self._bounds_width: float = 0.0
        self._bounds_height: float = 0.0
        self._bounds_left: float = 0.0
        self._bounds_bottom: float = 0.0

        # The rect is the area of the element that is actually utilised,
        # either divided among its children, or for its visual componenets
        self._rect: Rect = XYWH(0.0, 0.0, 0.0, 0.0)
        self._rect_width: float = 0.0
        self._rect_height: float = 0.0
        self._rect_left: float = 0.0
        self._rect_bottom: float = 0.0

        # -- AREA CONTROLS --

        # The anchors are fractional values which define the area of the bounds the element uses.
        # If the anchors have 0 area then the element won't change size along the axis with 0 size.
        self._anchors: Anchors = AnchorPresets.FULL
        # Offsets are unit values which represent offsets from the fractional anchors.
        self._offsets: Offsets = Offsets()
        # The size of the element in units is derived from the anchors and offsets along with the bounds
        self._size: Vec2 = Vec2()
        # The position of the element is the location of its center in units derived from the anchors and offsets along with the bounds
        self._position: Vec2 = Vec2()

        # -- PARENT INTERACTIONS --

        # The minimum size in units the element will accept from its parent
        self._min_size: Vec2 = minimum
        # How the Element should grow in size/position when its min_size changes
        self._growth_horizontal: AxisAnchor = AxisAnchor.BOTH
        self._growth_vertical: AxisAnchor = AxisAnchor.BOTH
        # The priority of this element as weighted against the priority of other elements.
        # When 0.0 or less it will only be given the minimum amount.
        self._priority: float = priority

        # -- CHILD INTERACTIONS --

        # Whether this Element has a layout defining property change and so needs to update it's children's bounds
        self._has_changed_layout: bool = False
        # This elements children:
        self._children: list[Element] = []

        # -- RENDERING AND EVENTS --
        self._tree: Tree | None = None
        self._depth: int = 0
        self._depth_offset: float = 0.0

        self._event_response: EventResponse = EventResponse.PASS

        # -- NAVIGATION --
        self._links: dict = {}  # TODO

        # -- VALUES --

        if bounds is not None:
            self.set_bounds(bounds)

        if anchors is not None:
            self.anchors = anchors

        if offsets is not None:
            self.offsets = offsets

        if size is not None:
            self.size = size

        if position is not None:
            self.position = position

    # |-- UTIL METHODS --|

    # -- LAYOUT PROPERTIES --

    @property
    def anchors(self) -> Anchors:
        return self._anchors

    @anchors.setter
    def anchors(self, anchors: Anchors) -> None:
        if anchors == self._anchors:
            return

        self._anchors = anchors
        self._recompute_rect()

        self._has_changed_layout = True

    @property
    def offsets(self) -> Offsets:
        return self._offsets

    @offsets.setter
    def offsets(self, offsets: Offsets) -> None:
        if offsets == self._offsets:
            return

        self._offsets = offsets
        self._recompute_rect()

        self._has_changed_layout = True

    @property
    def size(self) -> Vec2:
        return self._size

    @size.setter
    def size(self, size: Vec2) -> None:
        if size == self._size:
            return

        self._size = size
        self._rect = XYWH(self._position.x, self._position.y, size.x, size.y)
        self._recompute_offsets()

        self._has_changed_layout = True

    @property
    def position(self) -> Vec2:
        return self._position

    @position.setter
    def position(self, position: Vec2) -> None:
        if position == self._position:
            return

        self._position = position
        self._rect = XYWH(position.x, position.y, self._size.x, self._size.y)
        self._recompute_offsets()

        self._has_changed_layout = True

    @property
    def rect(self) -> Rect:
        return self._rect

    @rect.setter
    def rect(self, rect: Rect) -> None:
        if rect == self._rect:
            return

        self._rect = rect

        self._position = rect.center
        self._size = rect.size
        self._recompute_offsets()

        self._has_changed_layout = True

    @property
    def bounds(self) -> Rect | None:
        return self._bounds

    @bounds.setter
    def bounds(self, bounds: Rect) -> None:
        if bounds == self._bounds:
            return

        self._bounds = bounds
        self._recompute_rect()

        self._has_changed_layout = True

    @property
    def min_size(self) -> Vec2:
        return self._min_size

    @min_size.setter
    def min_size(self, min_size: Vec2) -> None:
        if min_size == self._min_size:
            return

        if self._bounds is not None and (
            self._min_size.x < min_size.x or self._min_size.y < min_size.y
        ):
            self._min_size = min_size
            self.set_bounds(self._bounds)
            return

        self._min_size = min_size

    # -- LAYOUT METHODS --

    def _recompute_rect(self):
        if self._bounds is None:
            left = right = bottom = top = 0.0
        else:
            left, bottom = self._bounds.uv_to_position(self._anchors.bottom_left)
            right, top = self._bounds.uv_to_position(self._anchors.top_right)

        offsets = self._offsets

        self._rect = LRBT(
            left + offsets.left,
            right + offsets.right,
            bottom + offsets.bottom,
            top + offsets.top,
        )
        self._position = self._rect.center
        self._size = self._rect.size

    def _recompute_offsets(self):
        if self._bounds is None:
            left = right = bottom = top = 0.0
        else:
            left, bottom = self._bounds.uv_to_position(self._anchors.bottom_left)
            right, top = self._bounds.uv_to_position(self._anchors.top_right)

        rect = self._rect

        self._offsets = Offsets(
            rect.left - left, rect.right - right, rect.bottom - bottom, rect.top - top
        )

    def set_bounds(self, raw_bounds: Rect):
        """
        A util method that helps make sure the bounds account for the elements growth attribute.

        This only works because Mint Elements are 'spillover'. A child's minimum size may be
        greater than its parent's. In which case the parent may be given less room than the child needs.

        Args:
            raw_bounds: The bounds rect that might be large enough for the rect.
        """
        l, r, b, t = raw_bounds.lrbt

        if raw_bounds.width < self._min_size.x:
            match self._growth_horizontal:
                case AxisAnchor.BEGINNING:
                    r = l + self._min_size.x
                case AxisAnchor.BOTH:
                    l = (l + r - self._min_size.x) / 2.0
                    r = (l + r + self._min_size.x) / 2.0
                case AxisAnchor.END:
                    l = r - self._min_size.x

        if raw_bounds.height < self._min_size.y:
            match self._growth_vertical:
                case AxisAnchor.BEGINNING:
                    t = b + self._min_size.y
                case AxisAnchor.BOTH:
                    b = (b + t - self._min_size.y) / 2.0
                    t = (b + t + self._min_size.y) / 2.0
                case AxisAnchor.END:
                    b = t - self._min_size.y

        self.bounds = LRBT(l, r, b, t)
        self._has_changed_layout = True

    # -- TREE PROPERTIES --

    @property
    def tree(self) -> Tree | None:
        return self._tree

    @property
    def depth(self) -> int:
        return self._depth

    # -- TREE METHODS --

    def _add_to_tree(self, tree: Tree | None, depth: int):
        if self._tree != None:
            self._remove_from_tree()
        self._depth = depth
        self._tree = tree

        if tree is not None:
            tree._add_element(self)
            self.__add_to_tree__(tree, depth)

        for child in self._children:
            child._add_to_tree(tree, depth + 1)

    def __add_to_tree__(self, tree: Tree | None, depth: int):
        pass

    def _remove_from_tree(self):
        if self._tree is None:
            return

        self.__remove_from_tree__()
        for child in self._children:
            child._remove_from_tree()

        self._tree._remove_element(self)
        self._tree = None

    def __remove_from_tree__(self):
        pass

    # |-- ELEMENT FUNCTIONALITY --|

    # -- LAYOUT METHODS --

    # Many of the element methods have a public private pair. This saves on boilerplate.
    def recompute_layout(self, force: bool = False, waterfall: bool = False):
        if self._has_changed_layout or force:
            self.__recompute_layout__()

        if waterfall:
            for child in self._children:
                child.recompute_layout(force, waterfall)

    def __recompute_layout__(self):
        # The overridable function that defines how children recieve their bounds from their parent.
        rect = self._rect
        for child in self._children:
            child.set_bounds(rect)

    def __recompute_width__(self):
        pass

    def __recompute_height__(self):
        pass

    def __recompute_position__(self):
        pass

    # -- CHILD METHODS --

    def add_child(self, child: Element) -> bool:
        if child in self._children or child is self:
            return False
        self._children.append(child)
        self.__add_child__(child)

        child._add_to_tree(self._tree, self._depth + 1)

        self._has_changed_layout = True
        return True

    def __add_child__(self, child: Element):
        pass

    def add_children(self, children: Iterable[Element]) -> bool:
        return all(self.add_child(child) for child in children)

    def remove_child(self, child: Element) -> bool:
        if child not in self._children:
            return False
        self._children.remove(child)
        self.__remove_child__(child)

        child._add_to_tree(None, 0)  # Makes the child the root of it's own tree.

        self._has_changed_layout = True
        return True

    def __remove_child__(self, child: Element):
        pass

    def remove_children(self, children: Iterable[Element]) -> bool:
        return all(self.remove_child(child) for child in children)

    def move_child(self, child: Element, idx: int) -> bool:
        if child not in self._children:
            return False
        if -len(self._children) <= idx < len(self._children):
            old = self._children.index(child)
            self._children[idx], self._children[old] = (
                self._children[old],
                self._children[idx],
            )
            self.__move_child__(child, idx)
            self._has_changed_layout = True
            return True
        return False

    def __move_child__(self, child: Element, idx: int):
        pass

    def insert_child(self, child: Element, idx: int) -> bool:
        if child in self._children:
            return False
        self._children.insert(idx, child)
        self.__insert_child__(child, idx)

        child._add_to_tree(self._tree, self.depth + 1)

        self._has_changed_layout = True
        return True

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def get_child_idx(self, child: Element) -> int:
        return self._children.index(child)

    def has_child(self, child: Element) -> bool:
        return child in self._children

    # -- EVENT METHODS --

    def fire_event(self, event: MintEvent) -> bool:
        match event._name:
            case BuiltInEvents.CURSOR_ENTER:
                return self.cursor_enter(event)  # type: ignore
            case BuiltInEvents.CURSOR_EXIT:
                return self.cursor_exit(event)  # type: ignore
            case BuiltInEvents.CURSOR_MOTION:
                return self.cursor_motion(event)  # type: ignore
            case BuiltInEvents.ACTION_INPUT:
                return self.action_input(event)  # type: ignore
            case BuiltInEvents.AXIS_CHANGE:
                return self.axis_changed(event)  # type: ignore
            case _:
                return self.custom_event(event)

    def cursor_enter(self, event: CursorMotionEvent) -> bool:
        captured = False
        for child in self._children[::-1]:
            captured = captured or child.cursor_enter(event)

        if captured:
            return True

        match self._event_response:
            case EventResponse.PASS:
                self.__on_cursor_enter__(event)
                return False
            case EventResponse.CAPTURE:
                self.__on_cursor_enter__(event)
                return True
            case EventResponse.BLOCK:
                return True
            case EventResponse.IGNORE:
                return False

    def cursor_exit(self, event: CursorMotionEvent) -> bool:
        captured = False
        for child in self._children[::-1]:
            captured = captured or child.cursor_exit(event)

        if captured:
            return True

        match self._event_response:
            case EventResponse.PASS:
                self.__on_cursor_exit__(event)
                return False
            case EventResponse.CAPTURE:
                self.__on_cursor_exit__(event)
                return True
            case EventResponse.BLOCK:
                return True
            case EventResponse.IGNORE:
                return False

    def cursor_motion(self, event: CursorMotionEvent) -> bool:
        captured = False
        for child in self._children[::-1]:
            captured = captured or child.cursor_motion(event)

        if captured:
            return True

        match self._event_response:
            case EventResponse.PASS:
                self.__on_cursor_motion__(event)
                return False
            case EventResponse.CAPTURE:
                self.__on_cursor_motion__(event)
                return True
            case EventResponse.BLOCK:
                return True
            case EventResponse.IGNORE:
                return False

    def action_input(self, event: ActionInputEvent) -> bool:
        captured = False
        for child in self._children[::-1]:
            captured = captured or child.action_input(event)

        if captured:
            return True

        match self._event_response:
            case EventResponse.PASS:
                self.__on_action_input__(event)
                return False
            case EventResponse.CAPTURE:
                self.__on_action_input__(event)
                return True
            case EventResponse.BLOCK:
                return True
            case EventResponse.IGNORE:
                return False

    def axis_changed(self, event: AxisChangeEvent) -> bool:
        captured = False
        for child in self._children[::-1]:
            captured = captured or child.axis_changed(event)

        if captured:
            return True

        match self._event_response:
            case EventResponse.PASS:
                self.__on_axis_changed__(event)
                return False
            case EventResponse.CAPTURE:
                self.__on_axis_changed__(event)
                return True
            case EventResponse.BLOCK:
                return True
            case EventResponse.IGNORE:
                return False

    def custom_event(self, event: MintEvent) -> bool:
        captured = False
        for child in self._children[::-1]:
            captured = captured or child.custom_event(event)

        if captured:
            return True

        match self._event_response:
            case EventResponse.PASS:
                self.__on_custom_event__(event)
                return False
            case EventResponse.CAPTURE:
                self.__on_custom_event__(event)
                return True
            case EventResponse.BLOCK:
                return True
            case EventResponse.IGNORE:
                return False

    def __on_cursor_enter__(self, event: CursorMotionEvent):
        pass

    def __on_cursor_exit__(self, event: CursorMotionEvent):
        pass

    def __on_cursor_motion__(self, event: CursorMotionEvent):
        pass

    def __on_cursor_click__(self, event: CursorClickEvent):
        pass

    def __on_cursor_drag__(self, event: CursorDragEvent):
        pass

    def __on_action_input__(self, event: ActionInputEvent):
        pass

    def __on_axis_changed__(self, event: AxisChangeEvent):
        pass

    def __on_custom_event__(self, event: MintEvent):
        pass

    # TODO: add more events
