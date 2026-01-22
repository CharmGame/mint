from __future__ import annotations
from enum import Enum
from uuid import UUID, uuid4


class GuiContext:
    def __init__(self) -> None:
        self._tree: Tree | None = None

    def preprocess(self):
        pass

    def enter_tree(self, tree: Tree):
        if self._tree is not None:
            self.exit_tree()
        self._tree = tree

    def exit_tree(self):
        # TODO: other stuff like close up the layouting maybe?
        self._tree = None

    def peek_stack(self) -> Element | None:
        if self._tree is None:
            raise ValueError('No tree currently')
        if not self._tree.___layout_stack__:
            return None
        return self._tree.___layout_stack__[-1]

    def get_depth(self) -> int:
        return 0 if self._tree is None else self._tree.__layout_depth__

    def enter_element(self, element: Element) -> None:
        if self._tree is None:
            raise ValueError('No tree currently')
        self._tree.enter_element(element)
    
    def exit_element(self) -> None:
        if self._tree is None:
            raise ValueError('No tree currently')
        self._tree.exit_element()

    def open_element(self, element: Element) -> None:
        if self._tree is None:
            # ????
            raise ValueError('No tree currently')
        self._tree.open_element(element)

    def close_element(self) -> None:
        if self._tree is None:
            # ????
            raise ValueError('No tree currently')
        self._tree.close_element()

    def has_open_element(self) -> bool:
        if self._tree is None or not self._tree.__layout_elements__:
            return False
        if self._tree.___layout_stack__ and (self._tree.__layout_elements__[-1] is self._tree.___layout_stack__[-1]):
            return False
        return not self._tree.__layout_elements__[-1]._closed

__context__ = GuiContext()


def initialise_gui():
    __context__.preprocess()


class Tree:

    def __init__(self) -> None:
        self.___layout_stack__: list[Element] = []
        self.__layout_elements__: list[Element] = []
        self.__layout_depth__: int = 0

    def layout(self):
        __context__.enter_tree(self)

        self.___layout_stack__ = []
        for e in self.__layout_elements__:
            e._parent = None
            e._children = []
        self.__layout_elements__ = []

        self.__layout__()
        if __context__.has_open_element():
            __context__.close_element()

        __context__.exit_tree()

    def open_element(self, element: Element):
        self.__layout_elements__.append(element)
        element.open()

    def close_element(self) -> None:
        if not self.__layout_elements__:
            raise ValueError('No elements being layed out')
        element = self.__layout_elements__[-1]
        if element._closed:
            return
        element._closed = True
        element.close()

    def enter_element(self, element: Element) -> None:
        self.___layout_stack__.append(element)
        self.__layout_depth__ += 1

    def exit_element(self):
        if self.__layout_depth__ == 0:
            raise ValueError('No elements to pop')
        element = self.___layout_stack__.pop()
        self.__layout_depth__ -= 1
        
        element._closed = True
        element.close()

    def draw(self):
        self.layout()
        print(
            '\n'.join(str(e) for e in self.__layout_elements__)
        )

    def __layout__(self): ...


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


class Element:

    def __init__(self, uid: str | UUID | None = None,
            *,
            minimum_size: tuple[float, float] = (0.0, 0.0),
            maximum_size: tuple[float, float] = (float('inf'), float('inf')),
            padding: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
            vertical_alignment: AxisAnchor = AxisAnchor.CENTER,
            horizontal_alignment: AxisAnchor = AxisAnchor.CENTER,
            priority: float = 1.0
        ) -> None:

        # Positional Values
        self.width: float = 0.0
        self.height: float = 0.0
        self.left: float = 0.0
        self.bottom: float = 0.0

        # Layout Values
        self.minimum_size: tuple[float, float] = minimum_size
        self.maximum_size: tuple[float, float] = maximum_size
        self.padding: tuple[float, float, float, float] = padding
        self.vertical_alignment: AxisAnchor = vertical_alignment
        self.horizontal_alignment: AxisAnchor = horizontal_alignment
        self.priority: float = priority

        self._parent: Element | None = __context__.peek_stack()
        self._children: list[Element] = []
        self._depth: int = __context__.get_depth()
        self._closed: bool = False

        if __context__.has_open_element():
            __context__.close_element()
        __context__.open_element(self)

    # -- BUILT-INS --

    def __enter__(self):
        __context__.enter_element(self)

    def __exit__(self, exec_type, exec_val, exec_tb) -> None:
        __context__.exit_element()

    def __str__(self):
        return f"|{"-"*self._depth} {self.__class__.__name__}"
    
    # -- FUNCTIONALITY --

    def open(self) -> None:
        if self._parent is not None:
            self._parent._children.append(self)
        self.__open__()

    def close(self) -> None:
        self.__close__()
    
    # -- OVERRIDEABLE --

    def __layout__(self):
        pass


    def __open__(self) -> None:
        pass

    def __close__(self) -> None:
        pass


class ScrollArea(Element):
    pass

class OverlapArea(Element):
    pass

class Array(Element):
    pass

class Anchor(Element):
    pass
