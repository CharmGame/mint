from __future__ import annotations
from sys import float_info
from contextlib import contextmanager
from typing import Any, Callable, Generator, Self, Sequence
from dataclasses import dataclass, field
from enum import IntEnum


# | -- UTIL -- |

__EPSILON = float_info.epsilon

@dataclass(slots=True)
class Vector2:
    x: float
    y: float

def _zero_vector() -> Vector2:
    return Vector2(0.0, 0.0)

def _one_vector() -> Vector2:
    return Vector2(1.0, 1.0)

@dataclass(slots=True)
class BoundingBox:
    left: float
    bottom: float
    width: float
    height: float

def _zero_bounds() -> BoundingBox:
    return BoundingBox(0.0, 0.0, 0.0, 0.0)


@dataclass(slots=True)
class Dimension:
    width: float
    height: float

    def __get_item__(self, idx: int):
        match idx:
            case 0:
                return self.width
            case 1:
                return self.height
        raise IndexError("Dimension only has two values (width, height)")


def _zero_dimension() -> Dimension:
    return Dimension(0.0, 0.0)


class Alignment(IntEnum):
    BEGINNING = LEFT = TOP = 0
    MIDDLE = CENTER = 1
    END = RIGHT = BOTTOM = 2


def clamp[T: Any](x: T, minimum: T, maximum: T) -> T:
    return min(maximum, max(minimum, x))


# | -- Sizing -- |


@dataclass(slots=True)
class Fixed:
    size: float

    @property
    def min(self) -> float:
        return self.size

    @property
    def max(self) -> float:
        return self.size


@dataclass(slots=True)
class Fit:
    min: float = 0
    max: float = float("inf")


@dataclass(slots=True)
class Grow:
    min: float = 0.0
    max: float = float("inf")
    fraction: float = 1.0

@dataclass(slots=True)
class Sizing:
    width: Fit | Grow | Fixed = field(default_factory=Fit)
    height: Fit | Grow | Fixed = field(default_factory=Fit)


# | -- Clipping -- |


@dataclass(slots=True)
class Clip:
    horizontal: bool = False
    vertical: bool = False
    child_offset: Vector2 = field(default_factory=_zero_vector)


# | -- Border -- |


@dataclass(slots=True)
class Padding:
    left: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    top: float = 0.0


# | -- LAYOUT -- |


class Layout:
    def __on_size_width__(self, element: TreeElement): ...

    def __on_size_height__(self, element: TreeElement): ...

    def __on_adjust_width__(self, element: TreeElement): ...

    def __on_adjust_height__(self, element: TreeElement): ...

    def __on_position_align_children__(self, element: TreeElement): ...

    def __on_declaration__(self) -> Element:
        # Create an element from the layout being used as `with Layout():`
        # Tree.compose. Can be overridden to modify the
        return Element(layout=self)

    def __enter__(self):
        declaration = self.__on_declaration__()
        tree = Tree.get_active_tree()
        tree.open_element(declaration)
        return declaration

    def __exit__(self, *_):
        tree = Tree.get_active_tree()
        tree.close_element()


# Places children within defined bounds with percent and pixel anchors
@dataclass(slots=True)
class Overlay(Layout):
    anchor_bottom: Vector2 = field(default_factory=_zero_vector)  # Bottom Left
    anchor_top: Vector2 = field(default_factory=_one_vector) # Top RIght
    offset_bottom: Vector2 = field(default_factory=_zero_vector)  # Bottom Left
    offset_top: Vector2 = field(default_factory=_zero_vector)  # Top Right


# Places children sequentially either horizontally or vertically
@dataclass(slots=True)
class Array(Layout):
    x: Alignment = Alignment.LEFT
    y: Alignment = Alignment.MIDDLE
    gutter: float = 0.0
    vertical: bool = False


    # TODO: create efficenient along axis and across axis generic functions
    def __on_size_width__(self, element: TreeElement):
        # The element was just closed so all of it's children have been defined and we can estimate
        # its width
        horizontal_padding = element.declaration.padding.left + element.declaration.padding.right

        dim = element.dimensions
        min_dim = element.min_dimensions
        not_clipped_h = not element.declaration.clip.horizontal
        if self.vertical:
            # The width of a vertical array is just the maximum child size.
            dim.width = min_dim.width = horizontal_padding
            for child in element.children:
                dim.width = max(dim.width, child.dimensions.width + horizontal_padding)
                if not_clipped_h:
                    min_dim.width = max(dim.width, child.min_dimensions.width + horizontal_padding)
        else:
            # The width of a horizontal array is the sum of the children's widths plus the guttering
            dim.width = min_dim.width = horizontal_padding
            for child in element.children:
                dim.width += child.dimensions.width
                if not_clipped_h:
                    min_dim.width += child.min_dimensions.width
            gutter = (len(element.children) - 1) * self.gutter
            dim.width += gutter
            if not_clipped_h:
                min_dim.width += gutter

    def __on_size_height__(self, element: TreeElement):
        # The element's content just readjusted the element's minimum height, and we need
        # recalculate the dimensions.
        vertical_padding = element.declaration.padding.bottom + element.declaration.padding.top
        dim = element.dimensions
        min_dim = element.min_dimensions
        not_clipped_v = not element.declaration.clip.vertical
        if self.vertical:
            # The height of a vertical array is the sum of the children's widths plus the guttering
            dim.height = min_dim.height = vertical_padding
            for child in element.children:
                dim.height += child.dimensions.height
                if not_clipped_v:
                    min_dim.height += child.min_dimensions.height
            gutter = (len(element.children) - 1) * self.gutter
            dim.height += gutter
            if not_clipped_v:
                min_dim.height += gutter
        else:
            # The height of a horizontal array is just the maximum child size.
            dim.height = min_dim.height = vertical_padding
            for child in element.children:
                dim.height = max(dim.height, child.dimensions.height + vertical_padding)
                if not_clipped_v:
                    min_dim.height = max(dim.height, child.min_dimensions.height + vertical_padding)

    def __on_adjust_width__(self, element: TreeElement):
        if self.vertical:
            self._adjust_off_axis(element)
        else:
            self._adjust_on_axis(element)

    def __on_adjust_height__(self, element: TreeElement):
        if self.vertical:
            self._adjust_on_axis(element)
        else:
            self._adjust_off_axis(element)

    def _adjust_on_axis(self, element: TreeElement):
        remaining_size = 0

        while remaining_size > __EPSILON:
            pass

        while remaining_size < -__EPSILON:
            pass

    def _adjust_off_axis(self, element: TreeElement):
        children = element.children
        # If the element is clipping in the off axis then we will be sizing
        # children based on the content size, not the size of the parent element
        # For Grow children, they are forced to be as large as possible then
        # all children are clamped to the sizing along the off axis
        content_size = 0
        if self.vertical:
            if element.declaration.clip.horizontal:
                content_size = max(c.dimensions.width for c in children)
            parent_size = element.dimensions.width - element.declaration.padding.left - element.declaration.padding.right
            max_size = max(parent_size, content_size)
            for child in children:
                if isinstance(child.declaration.sizing.width, Grow):
                    child.dimensions.width = min(max_size, child.declaration.sizing.width.max)
                child.dimensions.width = clamp(child.dimensions.width, child.min_dimensions.width, max_size)
        else:
            if element.declaration.clip.vertical:
                content_size = max(c.dimensions.height for c in children)
            parent_size = element.dimensions.height - element.declaration.padding.bottom - element.declaration.padding.top
            max_size = max(parent_size, content_size)
            for child in children:
                if isinstance(child.declaration.sizing.height, Grow):
                    child.dimensions.height = min(max_size, child.declaration.sizing.height.max)
                child.dimensions.height = clamp(child.dimensions.height, child.min_dimensions.height, max_size)

    def __on_position_align_children__(self, element: TreeElement):
        children = element.children
        if not children:
            return

        bounds = element.bounds
        padding = element.declaration.padding

        # Get the base offset, this is the clip offset and the padding in bottom left
        offset_x = bounds.left + padding.left + element.declaration.clip.child_offset.x
        offset_y = bounds.bottom + padding.bottom + element.declaration.clip.child_offset.y

        # The base space available
        available_width = bounds.width - padding.left - padding.right
        available_height = bounds.height - padding.bottom - padding.top

        # The general algo is direction agnostic
        # Along the array direction the available size is consumed by every child
        # Against the array direction the available size is shared by every child
        if self.vertical:
            available_height -= sum(c.dimensions.height for c in children)
            available_height -= (len(children) - 1) * self.gutter
            match self.y:
                case Alignment.TOP:
                    offset_y += available_height
                case Alignment.MIDDLE:
                    offset_y += available_height / 2
            for child in children[::-1]: # Flipped as GUI is usually designed top-down
                child.bounds.left = offset_x
                child.bounds.bottom = offset_y
                offset_y += child.dimensions.height + self.gutter
                match self.x:
                    case Alignment.CENTER:
                        child.bounds.left += (available_width - child.dimensions.width) / 2
                    case Alignment.RIGHT:
                        child.bounds.left += available_width - child.dimensions.width
        else:
            available_width -= sum(c.dimensions.width for c in children)
            available_width -= (len(children) - 1) * self.gutter
            match self.x:
                case Alignment.CENTER:
                    offset_x += available_width / 2
                case Alignment.RIGHT:
                    offset_x += available_width
            for child in children:
                child.bounds.left = offset_x
                child.bounds.bottom = offset_y
                offset_x += child.dimensions.width + self.gutter
                match self.y:
                    case Alignment.TOP:
                        child.bounds.bottom += available_height - child.dimensions.height
                    case Alignment.MIDDLE:
                        child.bounds.bottom += (available_height - child.dimensions.height) / 2


def Vertical(x: Alignment = Alignment.RIGHT, y: Alignment = Alignment.MIDDLE) -> Array:
    return Array(x, y, True)


def Horizontal(y: Alignment = Alignment.TOP, x: Alignment = Alignment.CENTER) -> Array:
    return Array(x, y, False)


# Places children sequentially up to a certain number before starting another row/column
@dataclass(slots=True)
class Grid(Layout):
    pass  # TODO


# TODO: Floating Element (i.e. Modal Window) that ignores parent's layout

# | -- Render Commands -- |

@dataclass
class RenderCommand:
    id: str

@dataclass(slots=True)
class OpenScissor(RenderCommand):
    region: BoundingBox

@dataclass(slots=True)
class CloseScissor(RenderCommand):
    pass

# | -- Content -- |


class Content:
    # TODO: provide min/max sizing functions for content

    def __on_declaration__(self) -> Element:
        # Create an element from content yielded during
        # Tree.compose. Can be overridden to modify the
        # defaults.
        return Element(content=self)

    def __on_wrap__(self, element: TreeElement) -> float | None:
        # Gets called after an element is sized horizontally.
        # should return the minimum width, or None if there is no change
        pass

    def __emit__(self, element: TreeElement, bounds: BoundingBox):
        # Gets called during the generation of render commands.
        raise NotImplementedError(f"{self} of type {type(self)} lacks `__emit__`")


@dataclass(slots=True)
class RenderRectCommand(RenderCommand):
    region: BoundingBox
    radius: tuple[float, float, float, float]


@dataclass(slots=True)
class Rect(Content):

    def __emit__(self, element: TreeElement, bounds: BoundingBox):
        return RenderRectCommand(element.id + "__rect__", bounds, (0, 0, 0, 0))


@dataclass(slots=True)
class RenderTextCommand(RenderCommand):
    anchor: Vector2
    text: str


@dataclass(slots=True)
class Text(Content):
    text: str

    def __emit__(self, element: TreeElement, bounds: BoundingBox):
        return RenderTextCommand(element.id + "__text__", Vector2(bounds.left, bounds.bottom), self.text)


@dataclass(slots=True)
class RenderImageCommand(RenderCommand):
    pass


@dataclass(slots=True)
class Image(Content):

    def __emit__(self, element: TreeElement, bounds: BoundingBox):
        return RenderImageCommand(element.id + "__image__")


# | -- Element -- |


@dataclass
class Element:
    sizing: Sizing = field(default_factory=Sizing)
    padding: Padding = field(default_factory=Padding)
    layout: Layout = field(default_factory=Array)
    content: Rect | Text | Image | Content = field(default_factory=Rect)
    clip: Clip = field(default_factory=Clip)
    id: str | None = None

    def __enter__(self) -> Self:
        # Open Element
        active_tree = Tree.get_active_tree()
        active_tree.open_element(self)
        return self

    def __exit__(self, *_):
        # Close Element
        active_tree = Tree.get_active_tree()
        active_tree.close_element()


# What types can be yielded in compose methods
type Composable = Element | Content
# What types can be used in `With` statements to layout the GUI tree
type Layoutable = Element | Layout
# The expected interface for a function passed to Tree.compose
type CompositionFunction = Callable[..., Generator[Composable, None, None]]


@dataclass
class TreeElement:
    id: str
    generation: int
    declaration: Element
    new: bool = True
    dimensions: Dimension = field(default_factory=_zero_dimension)
    min_dimensions: Dimension = field(default_factory=_zero_dimension)
    children: list[TreeElement] = field(default_factory=list)
    bounds: BoundingBox = field(default_factory=_zero_bounds)

    def __str__(self):
        return f"Element<{self.id}>"

    def __repr__(self) -> str:
        return self.__str__()


class Tree:

    def __init__(self, frame: Dimension | Sequence[float]) -> None:
        if not isinstance(frame, Dimension):
            frame = Dimension(frame[0], frame[1])
        self._frame: Dimension = frame
        self.generation: int = 0
        self._element_map: dict[str, TreeElement] = {}
        self._root: TreeElement = TreeElement("Root", -1, Element())

        self._elements: list[TreeElement] = []
        self._open_elements: list[TreeElement] = []

        self._render_commands: list = []

        # TODO: check if needed: render some vertical text and see if normal layouting works
        self._vertical_wrap_direction: bool = False

        self.set_active_tree()

    @staticmethod
    def get_active_tree() -> Tree:
        if _active_tree is None:
            raise ValueError(
                "No enabled tree. Ensure you are composing your GUI with tree.compose()."
            )

        return _active_tree

    def set_active_tree(self):
        global _active_tree
        _active_tree = self

    @contextmanager
    def activate(self) -> Generator[Any, None, None]:
        global _active_tree
        previous = _active_tree
        try:
            _active_tree = self
            self.begin_layout()
            yield self
        finally:
            self.finish_layout()
            _active_tree = previous

    def get_open_element(self) -> TreeElement:
        return self._open_elements[-1]

    def create_tree_element(self, declaration: Element) -> TreeElement:
        # If the element has not been given an id by the UI then make one that is ~persistent
        # across generations
        if declaration.id is None:
            parent = self.get_open_element()
            offset = len(parent.children)
            declaration.id = str(hash((parent.id, offset)))

        if declaration.id not in self._element_map:
            # New element that has never existed before
            element = TreeElement(declaration.id, self.generation + 1, declaration)
            self._element_map[element.id] = element
            return element

        # Element collision, this element was defined either in a previous generation of
        # the tree, or two elements have the same ID.
        hash_element = self._element_map[declaration.id]

        if hash_element.generation <= self.generation:
            # New generation of the same element. If the element is stale it is "new"
            hash_element.id = declaration.id
            hash_element.declaration = declaration
            hash_element.new = hash_element.generation < self.generation
            hash_element.generation = self.generation + 1
            hash_element.children.clear()
            # We don't update the bounds so it preserves the previous bounds.
            # Useful for interaction checks
            return hash_element

        raise KeyError(
            f"Two elements {self._element_map[declaration.id].declaration} and {declaration} have the same ID."
        )

    def open_element(self, declaration: Element):
        # Create the tree element, and register it with the Tree.
        element = self.create_tree_element(declaration)
        self._elements.append(element)
        self._open_elements.append(element)

        # TODO: handle adding current clip in stack

        # TODO: handle floating layouts if they need to be treated special in mint (they are in Clay)

        if declaration.clip.horizontal or declaration.clip.vertical:
            pass
            # TODO: handle adding new clip to stack

        return element

    def close_element(self):
        if not self._open_elements:
            return

        element = self._open_elements.pop()
        declaration = element.declaration
        if declaration.clip.horizontal or declaration.clip.vertical:
            # TODO: handle removing from clip stack, and maybe floating elements?
            pass

        # TODO: check if its worth it for fixed sizing elements to skip this
        declaration.layout.__on_size_width__(element)
        sizing_h = declaration.sizing.width
        element.dimensions.width = clamp(element.dimensions.width, sizing_h.min, sizing_h.max)

        if self._open_elements:
            # TODO: handle floating elements
            parent = self._open_elements[-1]
            parent.children.append(element)

    def begin_layout(self):
        self.generation += 1
        self._open_elements.clear()
        self._elements.clear()

        declaration = Element(
            Sizing(width=Fixed(self._frame.width), height=Fixed(self._frame.height)),
            id="__MintRoot",
        )

        element = self.open_element(declaration)
        self._root = element

    def finish_layout(self):
        self.close_element()

        assert not self._open_elements, "The tree failed to finish layouting as not all elements were closed."

        self.finalise_layout()

        # Remove stale elements.
        for key, item in tuple(self._element_map.items()):
            if item.generation > self.generation:
                continue
            del self._element_map[key]

    def finalise_layout(self, emit_commands: bool = True):
        # TODO see if caching the depth and breadth first inidces is worth it
        # that is: (0, 1, 1, 3, 3, 0) instead of making it on the fly
        commands = self._render_commands
        if emit_commands:
            commands.clear()

        # From top of the tree down adjust element width based on grow/fit sizing
        for element in self._elements:
            element.declaration.layout.__on_adjust_width__(element)

        # from bottom up use content calculate the minimum height of elements, and
        # vertically size the elements
        dfs_stack: list[TreeElement] = [self._root] # stack elements to visit
        dfs_open: list[str] = [] # Id of open elements
        while dfs_stack:
            element = dfs_stack[-1]
            if dfs_open and dfs_open[-1] == element.id:
                # TODO: check if its worth it for fixed sizing elements to skip this
                # On the way up size elements based on their children
                element.declaration.layout.__on_size_height__(element)
                sizing_v = element.declaration.sizing.height
                element.dimensions.height = clamp(element.dimensions.height, sizing_v.min, sizing_v.max)

                dfs_stack.pop()
                dfs_open.pop()
                continue
            dfs_stack.extend(element.children[::-1])
            dfs_open.append(element.id)

            # On the way down update all children's widths based on grow sizing
            element.declaration.layout.__on_adjust_width__(element)

            # Calculate the content's new minimum height, based on the element's width
            height = element.declaration.content.__on_wrap__(element)
            if height is not None:
                element.dimensions.height = max(height, element.dimensions.height)
                element.min_dimensions.height = max(height, element.min_dimensions.height)

        # from the top down adjust elements height based on grow sizing
        # From the top down as a stack position each element, and emit render commands
        dfs_stack.clear() # stack elements to visit
        dfs_open.clear() # Id of open elements
        dfs_stack.append(self._root)
        while dfs_stack:
            # Closing an open element
            element = dfs_stack[-1]
            bounds = element.bounds
            declaration = element.declaration
            if dfs_open and dfs_open[-1] == element.id:
                # The element was visited before and we are going back up the tree
                # This is where the end scissor command will be etc.

                if (declaration.clip.horizontal or declaration.clip.vertical) and emit_commands:
                    commands.append(CloseScissor(element.id + "__close_scissor__"))

                dfs_open.pop()
                dfs_stack.pop()
                continue
            dfs_open.append(element.id)
            dfs_stack.extend(element.children[::-1])

            element.declaration.layout.__on_adjust_height__(element)
            bounds.width = element.dimensions.width
            bounds.height = element.dimensions.height
            declaration.layout.__on_position_align_children__(element)
            if emit_commands:
                commands.append(declaration.content.__emit__(element, BoundingBox(bounds.left, bounds.bottom, bounds.width, bounds.height)))
                if declaration.clip.horizontal or declaration.clip.vertical:
                    # TODO: handle clip horizontal and vertical changing the actual scissor region
                    commands.append(OpenScissor(element.id + "__open_scissor__", BoundingBox(bounds.left, bounds.bottom, bounds.width, bounds.height)))

    def compose(self, composition: CompositionFunction):
        """
        Create an element tree declaratively. `mint.Tree.compose` is heavily inspired by
        the Textual compose functionality.

        Args:
            composable: A coroutine function which produces an iterable of composable objects.
        """
        compose_iter = iter(composition())
        # Allows exceptions raised in the `composition` function to be thrown properly
        # This comes directly from Textual.
        is_generator = hasattr(compose_iter, "throw")
        with self.activate():
            for child in compose_iter:
                # Type validation, and content transformation
                if isinstance(child, Element):
                    declaration = child
                elif isinstance(child, Content):
                    declaration = child.__on_declaration__()
                elif isinstance(child, Callable):
                    raise NotImplementedError("this is hard, for now use `yield from`")
                else:
                    # TODO: What happens with incorrect typing
                    exception = TypeError("Tree.compose only accepts Elements or Content")
                    if is_generator:
                        compose_iter.throw(exception)
                    else:
                        raise exception
                    continue

                try:
                    # Yielded elements have no children so open and close immediately
                    self.open_element(declaration)
                    self.close_element()
                except Exception as exception:
                    if is_generator:
                        compose_iter.throw(exception)
                    else:
                        raise exception

    def print_tree(self):
        element_stack: list[TreeElement] = [self._root]
        open_stack: list[str] = []
        while element_stack:
            element = element_stack[-1]
            if open_stack and open_stack[-1] == element.id:
                # Element already opened so close it
                open_stack.pop()
                element_stack.pop()
                indent = "    " * len(open_stack)
                print(f"{indent}Close({element.id})")
                continue

            # Element wasn't open and has children so let's open it properly
            indent = "    " * len(open_stack)
            print(f"{indent}Open({element.id}){type(element.declaration.layout)}{type(element.declaration.content)}")
            open_stack.append(element.id)
            element_stack.extend(element.children[::-1])


_active_tree: Tree | None = None