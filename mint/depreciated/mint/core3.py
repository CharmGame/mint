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


class Tree:
    pass

class Layout:
    pass

class Content:
    pass

class Element[L: Layout, C: Content]:
    
    def __init__(self, layout: L, content: C, parent: Element | None = None, uid: UUID | None = None) -> None:
        # The unique id that may last beyond the creation and destruction of multiple layout trees 
        self.uid: UUID = uid if uid is not None else uuid4()

        # The layout functionality of the element. Including how it will layout its children
        self._layout: L = layout

        # The renderable content of the element. 
        self._content: C = content

        # The bounds of a child element.
        # Mint layouts elements by width then height then position.
        self.width: float = 0.0
        self.height: float = 0.0
        self.left: float = 0.0
        self.bottom: float = 0.0

        # How many children deep the element is in the tree
        self._depth: int = 0

        # # All children of the element.
        # self._children: list[Element[ElementData]] = []

        # # Whether data has changed that would cause a layout update.
        # self._has_changed_layout: bool = True

        # # A weak reference to the parent as to not cause memory leaks.
        # self._parent = None
        # if parent is not None:
        #     parent.add_child(self)

    # -- LAYOUT FUNCTIONS --

    # -- EVENT RESPONSE --
