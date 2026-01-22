from __future__ import annotations
from enum import Enum, StrEnum
from uuid import uuid4, UUID
from typing import NamedTuple, Iterable, Protocol, Callable, Any, ClassVar, TypeVar
import dataclasses
import weakref

from arcade import Rect, LRBT, XYWH, Vec2, clock, Camera2D
from arcade.types import RGBA255
from arcade import Texture as ImageTexture

# -- TEMP DEBUG --

from random import randint
from pyglet.graphics import Batch
from pyglet.shapes import Rectangle
from arcade import get_window


# Rects generally with UV values (0.0 - 1.0)
type Anchors = Rect


# Unit values which represent axis aligned offsets from edges
class Offsets(NamedTuple):
    left: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    top: float = 0.0


# Useful anchor presets.
class AnchorPresets:
    FULL = LRBT(0.0, 1.0, 0.0, 1.0)
    ALL = LRBT(0.0, 1.0, 0.0, 1.0)
    CENTER = LRBT(0.5, 0.5, 0.5, 0.5)

    LEFT = LRBT(0.0, 0.0, 0.0, 1.0)
    RIGHT = LRBT(1.0, 1.0, 0.0, 1.0)
    BOTTOM = LRBT(0.0, 1.0, 0.0, 0.0)
    TOP = LRBT(0.0, 1.0, 1.0, 1.0)

    BOTTOM_LEFT = LRBT(0.0, 0.0, 0.0, 0.0)
    BOTTOM_RIGHT = LRBT(1.0, 1.0, 0.0, 0.0)
    TOP_LEFT = LRBT(0.0, 0.0, 1.0, 1.0)
    TOP_RIGHT = LRBT(1.0, 1.0, 1.0, 1.0)

    HORIZONTAL = LRBT(0.0, 1.0, 0.5, 0.5)
    VERTICAL = LRBT(0.5, 0.5, 0.0, 1.0)


# A 1 dimensional anchor enum for H/V Box, scaling etc
class AxisAnchor(Enum):
    BEGINNING = 0
    LEFT = 0
    TOP = 0

    CENTER = 1
    BOTH = 1
    MIDDLE = 1

    BOTTOM = 2
    RIGHT = 2
    END = 2


# TODO: Rename
class FrameFit(Enum):
    FIXED = 0  # The Frame will not change size even if the viewport grows in size. (I.E. no Zooming)
    STRETCH = 1  # The Frame will always fit on the vertical and horizontal even if units stop being square
    WIDTH = 2  # Fits so that the frame width matches the viewport irrespective of height
    HEIGHT = 3  # Fits so tha the frame height matches the viewport irrespective of width
    MAX = 4  # Fits so that the largest frame area is picked irrespective of if that spills outside viewport
    MIN = 5  # Fits so that the smallest frame area is picked. This insures no spillage occurs


# How elements should respond to events in the waterfall
class EventResponse(Enum):
    IGNORE = 0  # Won't trigger off event, but will pass to parent
    PASS = 1  # Will trigger off event, and will pass to parent
    CAPTURE = 2  # Will trigger off event, but won't pass to parent
    BLOCK = 3  # Won't trigger off event, and won't pass to parent


class BuiltInEvents(StrEnum):
    CURSOR_ENTER = "CursorEnterEvent"
    CURSOR_EXIT = "CursorExitEvent"
    CURSOR_MOTION = "CursorMotionEvent"
    CURSOR_CLICK = "CursorClickEvent"
    CURSOR_DRAG = "CursorDragEvent"
    ACTION_INPUT = "ActionInputEvent"
    AXIS_CHANGE = "AxisChangeEvent"


class BuiltInActions(StrEnum):
    LEFT_CLICK = "LEFT_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"


class BuiltInAxis(StrEnum):
    MOUSE_X = "MOUSE_X"
    MOUSE_Y = "MOUSE_Y"


class MintEvent:

    def __init__(self, *, time: float, name: str | None = None) -> None:
        self._time: float = time
        self._name: str = name or self.__class__.__name__


class CursorMotionEvent(MintEvent):

    def __init__(
        self, x: float, y: float, dx: float, dy: float, *, time: float
    ) -> None:
        MintEvent.__init__(self, time=time, name=BuiltInEvents.CURSOR_MOTION)
        self.x: float = x
        self.y: float = y
        self.dx: float = dx
        self.dy: float = dy


class CursorClickEvent(MintEvent):

    def __init__(self, x: float, y: float, action: str, pressed: bool, *, time: float):
        super().__init__(time=time, name=BuiltInEvents.CURSOR_CLICK)
        self.x: float = x
        self.y: float = y
        self.action: str = action
        self.pressed: bool = pressed


class CursorDragEvent(MintEvent):
    def __init__(self, x: float, y: float, dx: float, dy: float, action: str, *, time: float):
        super().__init__(time=time, name=BuiltInEvents.CURSOR_DRAG)
        self.x: float = x
        self.y: float = y
        self.dx: float = dx
        self.dy: float = dy
        self.action: str = action


class ActionInputEvent(MintEvent):

    def __init__(self, action: str, pressed: bool, *, time: float) -> None:
        MintEvent.__init__(self, time=time, name=BuiltInEvents.ACTION_INPUT)
        self.action: str = action
        self.pressed: bool = pressed


class AxisChangeEvent(MintEvent):  # TODO: N dimension axis

    def __init__(self, axis: str, v: float, dv: float, *, time: float) -> None:
        MintEvent.__init__(self, time=time, name=BuiltInEvents.AXIS_CHANGE)
        self.axis: str = axis
        self.delta_value: float = dv
        self.value: float = v


class Frame:

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.aspect = width / height


class Mint:
    """
    The Mint object acts as the root of an applications GUI.
    """

    RENDERABLES: ClassVar[dict[str, type[Renderable]]] = {}

    @staticmethod
    def register_renderable(name: str, renderable: type) -> None:
        if name in Mint.RENDERABLES:
            # TODO: Log??
            return
        Mint.RENDERABLES[name] = renderable

    def __init__(self) -> None:
        pass


def register_renderable(name: str, renderable: type[Renderable]) -> None:
    Mint.register_renderable(name, renderable)


class Tree:
    """
    Tree's are the root of rendering, animations, and events in Mint (mintree!).

    An element's units are all based on the tree's frame, and only 
    within the tree's viewport (or sub viewport) will be rendered.

    Tree's also hold the batch rendering objects for the various elements,
    and act as the link to the GL context for complex rendering operations.

    When an event is fired it runs breadth-first through the nodes in the tree.

    Elements not in a tree won't be drawn.

    # TODO: depth testing, and depth sorting
    """

    def __init__(self) -> None:
        # The aspect respecting frame that Unit's size are based on.
        self._frame: Frame = Frame(1280, 720)
        # The actual area rendered into. This doesn't need to match the frame.
        self._camera: Camera2D = Camera2D()
        # How the frame fits the viewport
        self._fit: FrameFit = FrameFit.MIN
        # The root Element of the Tree, will have its bounds equal to the viewport
        self._root: Element | None = None
        # The current max depth of the tree
        self._current_depth = 0
        # The layers of the tree from lowest (root) to highest depth
        self._layers: list[weakref.WeakSet[Element]] = []
        # All member elements of the tree mapped to their currently stored depth.
        self._members: dict[UUID, int] = {}
        # All created renderables in the Tree.
        self._renderables: dict[str, Renderable] = {}
        # Whether the Tree clears empty layers when an element is removed
        self._auto_prune: bool = True
        # The clock used internally by the tree for animations etc.
        self._clock: clock.Clock = clock.Clock()
        # The cursor position used for cursor enter/exit and motion events
        self._cursor: Vec2 = Vec2()
        # Track that the tree has changed in some way and the root need to layout
        self._tree_stale: bool = False

        # -- TEMP DEBUG --
        self._batch = Batch()
        self._context = get_window().ctx

    # -- FUNCTIONALITY METHODS --
    def _finalise_element_uid(self, uid: UUID) -> None:
        # We need a finaliser which doesn't reference the element
        # as that would mean the finaliser never fires.
        if uid not in self._members:
            return

        depth = self._members[uid]
        if not self._layers[depth] and self._auto_prune:
            self.prune(depth)
        del self._members[uid]

    # -- ELEMENT METHODS --

    def set_root(self, root: Element | None) -> None:
        if root is None:
            self.clear_root()
            return
        elif self._root is not None:
            self.clear_root()

        # Elements already impliment fully the functionality to
        # add/remove from the tree so this is easy.
        self._root = root
        self._add_element(root, 0)

    def clear_root(self) -> None:
        if self._root is None:
            return

        # Elements already impliment fully the functionality to
        # add/remove from the tree so this is easy.
        self._remove_element(self._root)

        # We force clear the renderables incase a custom element
        # forgets to remove itself from the renderable
        for renderable in self._renderables.values():
            renderable.clear()

        self._tree_stale = True

    def _add_element(self, element: Element, depth: int):
        """
        When a new child is added to an element within the tree we need to add it and all it's children.
        """
        uid = element.uid

        if element._tree is not None and element._tree != self:
            element._tree._remove_element(element)

        element._tree = self
        element._depth = depth

        self._tree_stale = True

        if depth == self._current_depth:
            self._layers.append(weakref.WeakSet())
            self._current_depth = len(self._layers)
        elif depth > self._current_depth:
            raise ValueError(f'The tree cannot accept an element with that depth as it would gaps')

        if uid not in self._members:
            self._layers[depth].add(element)
            self._members[uid] = depth

            # This helps insure the Tree discards an element correctly when it is no longer referenced
            finaliser = weakref.finalize(
                element, self._finalise_element_uid, uid
            )
            finaliser.atexit = False

            element.__add_to_tree__(self, depth)

            for child in element._children:
                self._add_element(child, depth + 1)
            return

        old = self._members[uid]
        element.__move_in_tree__(depth)

        if old == depth:
            for child in element._children:
                self._add_element(child, depth + 1)
            return

        self._layers[old].remove(element)
        self._layers[depth].add(element)

        for child in element._children:
            self._add_element(child, depth + 1)

    def _remove_element(self, element: Element):
        if element._tree != self:
            return

        uid = element.uid

        if uid not in self._members:
            return
        depth = self._members[uid]

        self._tree_stale = True

        element.__remove_from_tree__()
        for child in element._children:
            self._remove_element(child)

        self._layers[depth].remove(element)
        if not self._layers[depth] and self._auto_prune:
            self.prune(depth)
        del self._members[uid]

        element._tree = None

        # This doesn't get rid of the finaliser, but maybe that's okay?

    def prune(self, finish: int = 0) -> None:
        # Work from the end of the layers and remove all empty layers.
        # Does not handle floating layers (which should be impossible)
        for layer in self._layers[-1:finish:-1]:
            if layer:
                break
            self._layers.remove(layer)
        self._current_depth = len(self._layers)

    # -- RENDERABLE METHODS --

    def get_renderable(self, name: str) -> Renderable:
        if name not in self._renderables:
            self.add_renderable(name)

        return self._renderables[name]

    def add_renderable(self, name: str) -> None:
        if name in self._renderables:
            return

        if name not in Mint.RENDERABLES:
            raise ValueError(f"Renderable {name} not registered")

        self._renderables[name] = Mint.RENDERABLES[name]()

    def layout(self) -> None:
        if self._root is None:
            return

        self._root.width = self._camera.width
        self._root.height = self._camera.height
        self._root.left = 0.0
        self._root.bottom = 0.0

        self._root.layout()

        self._tree_stale = False

    # -- EVENT METHODS --

    def mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.cursor_motion(x, y, dx, dy)

    def custom_event(self, event: MintEvent): ...
    def cursor_motion(self, x: float, y: float, dx: float, dy: float):
        self._cursor = Vec2(x, y)
        # TODO: fire cursor motion event, then fire enter/exit events

    def enable_cursor(self): ... # TODO: fire enter events
    def disable_cursor(self): ... # TODO: fire exit events
    def axis_changed(self, action: str, v: float, dv: float): ... # TODO: fire axis changed events
    def action_input(self, action: str, pressed: bool): ... # TODO: fire action event

    # -- LOOP METHODS --

    def draw(self):
        if self._tree_stale:
            self.layout()

        with self._camera.activate():
            for renderable in self._renderables.values():
                renderable.draw()

    def update(self, dt: float):
        self._clock.tick(dt)
        # TODO: if cursor active, and controller active, move cursor
        # TODO: axis changed event

        # TODO: animations

    def update_viewport(self, width: int, height: int):
        self._camera.viewport = LRBT(0.0, width, 0.0, height)

        aspect = self._frame.aspect
        v_aspect = width / height

        base_w = self._frame.width
        base_h = self._frame.height

        match self._fit:
            case FrameFit.FIXED:
                w = width
                h = height
            case FrameFit.STRETCH:
                w = base_w
                h = base_h
            case FrameFit.WIDTH:
                w = base_w
                h = width * aspect
            case FrameFit.HEIGHT:
                w = height / aspect
                h = base_h
            case FrameFit.MAX:
                if aspect * height >= width:
                    w = v_aspect * base_h
                    h = base_h
                else:
                    w = base_w
                    h = base_w / v_aspect
            case FrameFit.MIN:
                if aspect * height < width:
                    w = v_aspect * base_h
                    h = base_h
                else:
                    w = base_w
                    h = base_w / v_aspect

        self._camera.projection = XYWH(0.0, 0.0, w, h)
        self._camera.position = 0.5 * w, 0.5 * h

        self._tree_stale = True


# |-- RENDERABLES --|


class Renderable(Protocol):
    # a Renderable's __init__ has to have no required arguments.

    def add(self, item: Any) -> None:
        pass

    def remove(self, item: Any) -> None:
        pass

    def draw(self) -> bool | None: ...

    def is_empty(self) -> bool: ...

    def is_full(self) -> bool:
        return False

    def clear(self) -> None: ...


class BuiltInRenderable(StrEnum):
    SPRITE = "builtin_sprite"
    TEXT = "builtin_text"
    BATCH = "builtin_batch"
    STYLE = "builtin_style"
    MESH = "builtin_mesh"


# |-- ELEMENTS --|


def _empty(*args: Any) -> None: ...

class DataConstructor(type):

    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]):
        typ = type.__new__(cls, name, bases, dct)
        return typ

        # We might still need metaclass logic so this sticks around.
        if bases == ():
            return typ
        return dataclasses.dataclass(typ)  # type: ignore -- Typ is a correct type promise.


class Data(metaclass=DataConstructor):

    def __init__(self) -> None: ...

    def __post_init__(self) -> None:
        Data.__init__(self)

    def update(self, other: Data) -> None:
        pass


"""
# The anchors are fractional values which define the area of the bounds the element uses.
# If the anchors have 0 area then the element won't change size along the axis with 0 size.
anchors: Anchors = AnchorPresets.FULL
# Offsets are unit values which represent offsets from the fractional anchors.
offsets: Offsets = Offsets()
# The position of the element is the location of its center in units derived from the anchors and offsets along with the bounds
position: Vec2 = Vec2()
# The size of the element in units is derived from the anchors and offsets along with the bounds
size: Vec2 = Vec2()
"""

@dataclasses.dataclass
class ElementData(Data):
    """
    The Data in here and any sub-classes can all be modified and animated by Mint.
    """

    # -- SIZING --

    # The minimum width of the element's bounds
    minimum_width: float = 0.0

    # The minimum height of the element's bounds
    minimum_height: float = 0.0

    # The maximum width of the element's bounds
    maximum_width: float = float('inf')

    # The maximum height of the element's bounds
    maximum_height: float = float('inf')

    # Padding
    padding: Offsets = Offsets()

    # The fraction of the parent the element wants.
    # A priority of 0 means the parent will never assign
    # the child more than it has requested
    priority: float = 1.0

    # -- Positioning --

    # How the element wants to be placed within it's parent if there is room for it
    horizontal_alignmnet: AxisAnchor = AxisAnchor.CENTER
    vertical_alignment: AxisAnchor = AxisAnchor.CENTER

    # -- EVENTS --

    # How the element should pass events down to parents.
    event_response: EventResponse = EventResponse.PASS

    # Actual event response methods. These can be manipulated by animations and state controls.
    on_cursor_motion: Callable[[Element, CursorMotionEvent], Any] = _empty
    on_cursor_enter: Callable[[Element, CursorMotionEvent], Any] = _empty
    on_cursor_exit: Callable[[Element, CursorMotionEvent], Any] = _empty
    on_cursor_click: Callable[[Element, CursorClickEvent], Any] = _empty
    on_cursor_drag: Callable[[Element, CursorDragEvent], Any] = _empty
    on_action_input: Callable[[Element, ActionInputEvent], Any] = _empty
    on_axis_changed: Callable[[Element, AxisChangeEvent], Any] = _empty
    on_custom_event: Callable[[Element, MintEvent], Any] = _empty

    def create(self, parent: Element | None = None, uid: UUID | None = None) -> Element:
        return Element(self, parent, uid)

class Layout:
    """
    A Mint component that describes how its children should be placed.
    An element is ultimately composable and so this can vary over time.
    either it's internal values, or the entire layout.
    """
    pass

class Content:
    """
    A Mint component that describes what should be drawn. When the Mint tree is
    composed these use their owner element's size, location, and styling to 
    add themselves to the render pipeline. This is currently based on pyglet batches
    but will eventually be a hot-swappable sytstem.
    """
    pass

class Element[D: ElementData]: # TODO: make a type var for element data
    def __init__(self, data: D, parent: Element | None = None, uid: UUID | None = None):
        self.uid: UUID = uid if uid is not None else uuid4()

        # The bounds of a child element.
        # Mint layouts elements by width then height then position.
        self.width: float = 0.0
        self.height: float = 0.0
        self.left: float = 0.0
        self.bottom: float = 0.0

        # The element data that is animatable and state controlled.
        self._data: D = data

        # The tree the element belongs too
        self._tree: Tree | None = None

        # How many children deep the element is in the tree
        self._depth: int = 0

        # All children of the element.
        self._children: list[Element[ElementData]] = []

        # Whether data has changed that would cause a layout update.
        self._has_changed_layout: bool = True

        # A weak reference to the parent as to not cause memory leaks.
        self._parent = None
        if parent is not None:
            parent.add_child(self)

    # -- TREE METHODS --

    def __add_to_tree__(self, tree: Tree | None, depth: int): ...
    def __move_in_tree__(self, depth: int): self.__add_to_tree__(self._tree, depth)
    def __remove_from_tree__(self): ...

    def __add_child__(self, child: Element): ...
    def __remove_child__(self, child: Element): ...
    def __move_child__(self, child: Element, idx: int): ...
    def __insert_child__(self, child: Element, idx: int): self.__add_child__(child)

    def add_child(self, child: Element) -> bool:
        if child in self._children or child is self:
            return False
        self._children.append(child)
        self.__add_child__(child)

        if self._tree is not None:
            self._tree._add_element(child, self._depth + 1)

        self._has_changed_layout = True
        return True

    def add_children(self, children: Iterable[Element]) -> bool:
        return all(self.add_child(child) for child in children)

    def remove_child(self, child: Element) -> bool:
        if child not in self._children:
            return False
        self._children.remove(child)
        self.__remove_child__(child)

        if self._tree is not None:
            self._tree._remove_element(child)

        self._has_changed_layout = True
        return True

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

    def insert_child(self, child: Element, idx: int) -> bool:
        if child in self._children:
            return False
        self._children.insert(idx, child)
        self.__insert_child__(child, idx)

        if self._tree is not None:
            self._tree._add_element(child, self._depth + 1)

        self._has_changed_layout = True
        return True

    def get_child_idx(self, child: Element) -> int:
        return self._children.index(child)

    def has_child(self, child: Element) -> bool:
        return child in self._children

    # -- LAYOUT METHODS --

    def place(self, left: float, bottom: float, width: float, height: float):
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height

        self.layout()

    def layout(self) -> None:
        # Starting from the leaves of the tree get the ideal widths of the elements
        # Then from the root squish/stretch elements widths untill they fit
        # after squishing and stretching elements ensure elements wrap their componenets correctly (basically just text)
        # Starting from the leaves of the tree again get the ideal heights of the elements
        # Then from the root squish/stretch element's heights untill everything fits.
        # Finally place elements along with anchoring

        # As the element at the top we don't need to find it's width just find the
        # width of children
        for child in self._children:
            child.layout_horizontal()
        self.compress_width()

        self.layout_wrapping()
        for child in self._children:
            child.layout_wrapping()
            child.layout_vertical()

        self.compress_height()

        self.layout_position()

        self.update_style()

    def layout_horizontal(self) -> float:
        data = self._data
        padding_width = data.padding.left + data.padding.right
        child_width = data.minimum_width - padding_width
        for child in self._children:
            child_width = max(child_width, child.layout_horizontal())
        self.width = min(padding_width + child_width, data.maximum_width)

        return self.width

    def compress_width(self) -> None:
        data = self._data
        padding_width = data.padding.left + data.padding.right
        child_width = self.width - padding_width
        for child in self._children:
            if child._data.priority != 0:
                child.width = max(child._data.minimum_width, min(child._data.maximum_width, child_width))
            child.compress_width()

    def layout_vertical(self) -> float:
        data = self._data
        padding_height = data.padding.top + data.padding.bottom
        child_height = data.minimum_height - padding_height
        for child in self._children:
            child_height = max(child_height, child.layout_vertical())
        self.height = min(padding_height + child_height, data.maximum_height)

        return self.height

    def compress_height(self) -> None:
        data = self._data
        padding_height = data.padding.top + data.padding.bottom
        child_height = self.height - padding_height
        for child in self._children:
            if child._data.priority != 0:
                child.height = max(child._data.minimum_height, min(child._data.maximum_height, child_height))
            child.compress_height()

    def layout_position(self) -> None:
        data = self._data
        padless_width = self.width - data.padding.left - data.padding.right
        padless_height = self.height - data.padding.bottom - data.padding.top
        padded_left = self.left + data.padding.left
        padded_bottom = self.bottom + data.padding.bottom
        for child in self._children:
            excess_width = padless_width - child.width
            excess_height = padless_height - child.height
            match child._data.horizontal_alignmnet:
                case AxisAnchor.LEFT:
                    child.left = padded_left
                case AxisAnchor.CENTER:
                    child.left = padded_left + (excess_width / 2.0)
                case AxisAnchor.RIGHT:
                    child.left = padded_left + excess_width

            match child._data.vertical_alignment:
                case AxisAnchor.BOTTOM:
                    child.bottom = padded_bottom
                case AxisAnchor.CENTER:
                    child.bottom = padded_bottom + (excess_height / 2.0)
                case AxisAnchor.TOP:
                    child.bottom = padded_bottom + excess_height

            child.layout_position()

    def layout_wrapping(self) -> None:
        for child in self._children:
            child.layout_wrapping()

    def update_style(self) -> None:
        for child in self._children:
            child.update_style()

    # -- EVENT METHODS --

    def custom_event(self, event: MintEvent): ...
    def cursor_enter(self, event: CursorMotionEvent): ...
    def cursor_exit(self, event: CursorMotionEvent): ...
    def cursor_hover(self, event: CursorMotionEvent): ...
    def cursor_click(self, event: CursorClickEvent): ...
    def cursor_drag(self, event: CursorDragEvent): ...
    def action_input(self, event: ActionInputEvent): ...
    def axis_changed(self, event: AxisChangeEvent): ...


# -- ELEMENTS --

# -- | -- LAYOUT -- | --
@dataclasses.dataclass
class ArrayElement(ElementData):
    anchor: AxisAnchor = AxisAnchor.BEGINNING
    vertical: bool = False
    flip_fill_order: bool = False
    child_padding: float = 0.0
    scroll: float = 0.0
    contained: bool = False

    def create(self, parent: Element | None = None, uid: UUID | None = None) -> Array:
        return Array(self, parent, uid)

class Array(Element[ArrayElement]):
    def _layout_axis(self, y_axis: bool) -> float:
        data = self._data

        list_axis = y_axis == data.vertical

        spacing = 0.0 if not list_axis else len(self._children) * data.child_padding
        if y_axis:
            padding = data.padding.bottom + data.padding.top
        else:
            padding = data.padding.left + data.padding.right

        child_size = 0.0
        for child in self._children:
            if y_axis:
                size = child.layout_vertical()
            else:
                size = child.layout_horizontal()

            if list_axis:
                child_size += size
            else:
                child_size = max(child_size, size)

        size = child_size + padding + spacing

        if y_axis:
            self.height = min(data.maximum_height, min(data.minimum_height, size))
            return self.height
        self.width = min(data.maximum_width, max(data.minimum_width, size))
        return self.width

    def _compress_off_axis(self, y_axis: bool):
        data = self._data
        if y_axis:
            free_size = self.height - data.padding.top - data.padding.bottom
        else:
            free_size = self.width - data.padding.left - data.padding.right

        for child in self._children:
            if y_axis:
                child.height = min(child._data.maximum_height, max(child._data.minimum_height, free_size))
            else:
                child.width = min(child._data.maximum_width, max(child._data.minimum_width, free_size))

    def _compress_axis(self, y_axis: bool) -> None:
        active_children = [child for child in self._children if child._data.priority != 0] # Start with all children active. We will be pruning this list
        data = self._data

        if y_axis:
            remaining_size = self.height - data.padding.top - data.padding.bottom
            remaining_size = remaining_size - sum(child.height for child in self._children)
        else:
            remaining_size = self.width - data.padding.left - data.padding.right
            remaining_size = remaining_size - sum(child.width for child in self._children)
        remaining_size = remaining_size - (len(self._children) - 1) * data.child_padding

        growing = remaining_size >= 0

        while (abs(remaining_size) > 1e-10 and active_children):
            if y_axis:
                set_size = active_children[0].height
            else:
                set_size = active_children[0].width

            if growing:
                next_size = float('inf')
            else:
                next_size = 0
            size_to_add = remaining_size
            priority = 0

            for child in active_children:
                if y_axis:
                    size = child.height / child._data.priority
                else:
                    size = child.width / child._data.priority

                if growing:
                    if size < set_size:
                        next_size = set_size
                        set_size = size
                    elif size > set_size:
                        next_size = min(next_size, size)
                        size_to_add = next_size - set_size
                else:
                    if set_size < size:
                        next_size = set_size
                        set_size = size
                    elif size < set_size:
                        next_size = max(next_size, size)
                        size_to_add = next_size - set_size

                priority += child._data.priority

            if growing:
                size_to_add = min(size_to_add, remaining_size / priority)
            else:
                size_to_add = max(size_to_add, remaining_size / priority)

            for child in active_children[:]:
                prev_size = child.height if y_axis else child.width
                if (prev_size == set_size * child._data.priority):
                    if y_axis:
                        child.height += size_to_add * child._data.priority
                        if child.height <= child._data.minimum_height:
                            child.height = child._data.minimum_height
                            active_children.remove(child)
                        if child._data.maximum_height <= child.height:
                            child.height = child._data.maximum_height
                            active_children.remove(child)
                        remaining_size -= (child.height - prev_size)
                    else:
                        child.width += size_to_add
                        if child.width <= child._data.minimum_width:
                            child.width = child._data.minimum_width
                            active_children.remove(child)
                        if child._data.maximum_width <= child.width:
                            child.width = child._data.maximum_width
                            active_children.remove(child)
                        remaining_size -= (child.width - prev_size)

    def layout_horizontal(self) -> float:
        return self._layout_axis(False)

    def compress_width(self) -> None:
        if self._data.vertical:
            self._compress_off_axis(False)
        else:
            self._compress_axis(False)

        for child in self._children:
            child.compress_width()

    def layout_vertical(self) -> float:
        return self._layout_axis(True)

    def compress_height(self) -> None:
        if self._data.vertical:
            self._compress_axis(True)
        else:
            self._compress_off_axis(True)

        for child in self._children:
            child.compress_height()

    def layout_position(self) -> None:
        if not self._children:
            return

        data = self._data
        y_axis = data.vertical

        if data.flip_fill_order:
            children = self._children[::-1]
        else:
            children = self._children

        padless_width = self.width - data.padding.left - data.padding.right
        padless_height = self.height - data.padding.bottom - data.padding.top
        padded_left = self.left + data.padding.left
        padded_bottom = self.bottom + data.padding.bottom
        padding = data.child_padding * (len(children) - 1)

        if y_axis:
            child_size = padding + sum(child.height for child in children)
            fraction = padless_height / child_size if (data.contained and padless_height < child_size) else 1.0
            match data.anchor:
                case AxisAnchor.BOTTOM:
                    offset = padded_bottom
                case AxisAnchor.MIDDLE:
                    offset = padded_bottom + (padless_height - child_size * fraction) / 2.0
                case AxisAnchor.TOP:
                    offset = padded_bottom + (padless_height - child_size * fraction)
        else:
            child_size = padding + sum(child.width for child in children)
            fraction =  padless_width / child_size if (data.contained and padless_width < child_size) else 1.0
            match data.anchor:
                case AxisAnchor.LEFT:
                    offset = padded_left
                case AxisAnchor.MIDDLE:
                    offset = padded_left + (padless_width - child_size * fraction) / 2.0
                case AxisAnchor.RIGHT:
                    offset = padded_left + (padless_width - child_size * fraction)

        position = 0
        for child in self._children:
            if y_axis:
                excess_width = padless_width - child.width
                child.bottom = offset + position
                position += child.height + data.child_padding
                match child._data.horizontal_alignmnet:
                    case AxisAnchor.LEFT:
                        child.left = padded_left
                    case AxisAnchor.CENTER:
                        child.left = padded_left + (excess_width / 2.0)
                    case AxisAnchor.RIGHT:
                        child.left = padded_left + excess_width
            else:
                excess_height = padless_height - child.height
                child.left = offset + position
                position += child.width + data.child_padding
                match child._data.vertical_alignment:
                    case AxisAnchor.BOTTOM:
                        child.bottom = padded_bottom
                    case AxisAnchor.CENTER:
                        child.bottom = padded_bottom + (excess_height / 2.0)
                    case AxisAnchor.TOP:
                        child.bottom = padded_bottom + excess_height

            child.layout_position()


@dataclasses.dataclass
class GridElement(ElementData):
    horizontal_anchor: AxisAnchor = AxisAnchor.BEGINNING
    vertical_anchor: AxisAnchor = AxisAnchor.BEGINNING
    vertical: bool = False
    flip_column_order: bool = False
    flip_row_order: bool = False
    repeat_count: int = 0
    column_padding: float = 0.0
    row_padding: float = 0.0

class Grid(Element[GridElement]): ...


@dataclasses.dataclass
class AnchorElement(ElementData):
    left_anchor: float = 0.0
    right_anchor: float = 0.0
    bottom_anchor: float = 0.0
    top_anchor: float = 0.0

    left_offset: float = 0.0
    right_offset: float = 0.0
    bottom_offset: float = 0.0
    top_offset: float = 0.0

class Anchor(Element[AnchorElement]):
    
    def layout_horizontal(self) -> float:
        data = self._data
        padding_width = data.padding.left + data.padding.right
        child_width = data.minimum_width - padding_width
        for child in self._children:
            child_width = max(child_width, child.layout_horizontal())
        self.width = min(padding_width + child_width, data.maximum_width)

        return self.width

    def compress_width(self) -> None:
        data = self._data
        padding_width = data.padding.left + data.padding.right
        child_width = self.width - padding_width
        for child in self._children:
            if child._data.priority != 0:
                child.width = max(child._data.minimum_width, min(child._data.maximum_width, child_width))
            child.compress_width()

    def layout_vertical(self) -> float:
        data = self._data
        padding_height = data.padding.top + data.padding.bottom
        child_height = data.minimum_height - padding_height
        for child in self._children:
            child_height = max(child_height, child.layout_vertical())
        self.height = min(padding_height + child_height, data.maximum_height)

        return self.height

    def compress_height(self) -> None:
        data = self._data
        padding_height = data.padding.top + data.padding.bottom
        child_height = self.height - padding_height
        for child in self._children:
            if child._data.priority != 0:
                child.height = max(child._data.minimum_height, min(child._data.maximum_height, child_height))
            child.compress_height()

    def layout_position(self) -> None:
        data = self._data
        padless_width = self.width - data.padding.left - data.padding.right
        padless_height = self.height - data.padding.bottom - data.padding.top
        padded_left = self.left + data.padding.left
        padded_bottom = self.bottom + data.padding.bottom
        for child in self._children:
            excess_width = padless_width - child.width
            excess_height = padless_height - child.height
            match child._data.horizontal_alignmnet:
                case AxisAnchor.LEFT:
                    child.left = padded_left
                case AxisAnchor.CENTER:
                    child.left = padded_left + (excess_width / 2.0)
                case AxisAnchor.RIGHT:
                    child.left = padded_left + excess_width

            match child._data.vertical_alignment:
                case AxisAnchor.BOTTOM:
                    child.bottom = padded_bottom
                case AxisAnchor.CENTER:
                    child.bottom = padded_bottom + (excess_height / 2.0)
                case AxisAnchor.TOP:
                    child.bottom = padded_bottom + excess_height

            child.layout_position()

    def layout_wrapping(self) -> None:
        for child in self._children:
            child.layout_wrapping()

    def update_style(self) -> None:
        for child in self._children:
            child.update_style()

# -- | -- VISUAL -- | --
class StyleBoxElement(ElementData):
    corners: tuple[float, float, float, float]
    borders: tuple[float, float, float, float]
    color: RGBA255 = (255, 255, 255, 255)
    border_color: RGBA255 = (255, 255, 255, 255)
    gradient: bool = False
    corners_pinned_out: bool = False
    resolution: int = 12

class TextElement(ElementData):
    text: str
    font_name: str
    font_size: float
    color: RGBA255 = (255, 255, 255, 255)


class TextureElement(ElementData):
    texture: ImageTexture
    fit: FrameFit
    color: RGBA255 = (255, 255, 255, 255)
    angle: float = 0.0
