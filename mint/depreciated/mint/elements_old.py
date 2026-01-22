from __future__ import annotations
from uuid import UUID
from typing import Literal
from math import ceil

from arcade import Vec2, Sprite, load_texture, Text, color, LRBT, LBWH
from arcade.types import Color, RGBOrA255, RGBA255

from charm.lib.mint.implementations.arcade_stylebox import StyleBox

from .core import (
    BuiltInRenderable,
    Tree,
    Element,
    AxisAnchor,
    Anchors,
    Offsets,
    EventResponse,
    FrameFit,
    MintEvent,
    CursorMotionEvent,
    ActionInputEvent,
    AxisChangeEvent
)


__all__ = (
    "ListElement",
    "GridElement",
    "TextureElement",
    "LabelElement"
)

class _TEMPLATE(Element):

    def __init__(self,
                 *,
                 bounds: Anchors | None = None,
                 minimum: Vec2 = Vec2(),
                 priority: float = 1.0,
                 anchors: Anchors | None = None,
                 offsets: Offsets | None = None,
                 size: Vec2 | None = None,
                 position: Vec2 | None = None,
                 uid: UUID | None = None
            ) -> None:
        super().__init__(bounds=bounds, minimum=minimum, priority=priority, anchors=anchors, offsets=offsets, size=size, position=position, uid=uid)

    def __recompute_layout__(self):
        rect = self._rect
        for child in self._children:
            child.set_bounds(rect)

    def __add_to_tree__(self, tree: Tree | None, depth: int):
        pass

    def __remove_from_tree__(self):
        pass

    def __add_child__(self, child: Element):
        pass

    def __remove_child__(self, child: Element):
        pass

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def __move_child__(self, child: Element, idx: int):
        pass

    def __on_cursor_enter__(self, event: CursorMotionEvent):
        pass
    
    def __on_cursor_exit__(self, event: CursorMotionEvent):
        pass

    def __on_cursor_motion__(self, event: CursorMotionEvent):
        pass

    def __on_action_input__(self, event: ActionInputEvent):
        pass

    def __on_axis_changed__(self, event: AxisChangeEvent):
        pass

    def __on_custom_event__(self, event: MintEvent):
        pass


# -- LAYOUT ELEMENTS --

# TODO
class ListElement(Element):

    def __init__(
            self,
            anchor: AxisAnchor = AxisAnchor.BEGINNING,
            vertical: bool = False,
            padding: float = 0.0,
            flip_fill_order: bool = False,
            uniform: bool = False,
            contained: bool = True,
            *,
            bounds: Anchors | None = None,
            minimum: Vec2 = Vec2(),
            priority: float = 1.0,
            anchors: Anchors | None = None,
            offsets: Offsets | None = None,
            size: Vec2 | None = None,
            position: Vec2 | None = None,
            uid: UUID | None = None
        ) -> None:
        super().__init__(bounds=bounds, minimum=minimum, priority=priority, anchors=anchors, offsets=offsets, size=size, position=position, uid=uid)
        self._anchor: AxisAnchor = anchor
        self._focus: Element | None = None
        self._vertical: bool = vertical
        self._padding: float = padding
        self._flip: bool = flip_fill_order
        self._uniform: bool = uniform
        self._contained: bool = contained

    def __recompute_layout__(self):
        if not self._children:
            return
        rect = self._rect
        width = rect.width
        height = rect.height
        children = self._children

        primary_size, secondary_size = (height, width) if self._vertical else (width, height)
        size_axis = 1 if self._vertical else 0

        # Primary Sizing

        sizes = [child._min_size[size_axis] for child in children]

        total_priority = sum(child._priority for child in children)
        padding = self._padding * (len(children) - 1)

        active_children = list(idx for idx, child in enumerate(children) if child._priority != 0.0)
        fixed_size = sum(child._min_size[size_axis] for child in children if child._priority == 0.0)

        excess = primary_size - padding - fixed_size
        remaing = primary_size - padding - sum(sizes)

        while remaing > 0.0 and active_children:
            sizes = [child._min_size[size_axis] for child in children]
            for idx in active_children:
                child = children[idx]
                size = excess * child._priority / total_priority
                if size < child._min_size[size_axis]:
                    # When the child can't fit we give it the min size, and restart.
                    total_priority -= child._priority
                    fixed_size += child._min_size[size_axis]
                    active_children.remove(idx)
                    break
                sizes[idx] = size
            else:
                break

            excess = height - padding - fixed_size
            remaing = height - padding - sum(sizes)

        # placing everything
        elements_size = padding + sum(sizes)
        fraction = primary_size / elements_size if (self._contained and elements_size > primary_size) else 1.0 

        if self._flip:
            children = children[::-1]
            sizes = sizes[::-1]

        pos = 0
        offset = 0
        if self._vertical:
            match self._anchor:
                case AxisAnchor.TOP:
                    offset = primary_size
                case AxisAnchor.CENTER:
                    offset = (primary_size + elements_size * fraction) * 0.5
                case AxisAnchor.BOTTOM:
                    offset = elements_size * fraction

            focus = 0.0
            if self._focus is not None:
                
                start = rect.bottom + offset
                for child, child_height in zip(children, sizes):
                    if child == self._focus:
                        break
                    pos -= (child_height + self._padding) * fraction

            start = rect.bottom + offset + focus
            for child, child_height in zip(children, sizes):
                child.set_bounds(LBWH(rect.left, start - pos - child_height, width, child_height))
                pos += (child_height + self._padding) * fraction
        else:
            match self._anchor:
                case AxisAnchor.RIGHT:
                    offset = 0.0
                case AxisAnchor.CENTER:
                    offset = (primary_size - elements_size * fraction) * 0.5
                case AxisAnchor.LEFT:
                    offset = primary_size - elements_size * fraction
            start = rect.left + offset
            for child, child_width in zip(children, sizes):
                child.set_bounds(LBWH(start + pos, rect.bottom, child_width, height))
                pos += (child_width + self._padding) * fraction


    def __add_to_tree__(self, tree: Tree | None, depth: int):
        pass

    def __remove_from_tree__(self):
        pass

    def __add_child__(self, child: Element):
        pass

    def __remove_child__(self, child: Element):
        pass

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def __move_child__(self, child: Element, idx: int):
        pass


class GridElement(Element):

    def __init__(self,
                 wrap: int, # After how many Columns/Rows should the grid wrap?
                 count: int = -1, # How many elements, if -1 then there is no maximum number of elements. When the max is reached the positions start being repeated
                 column_padding: float = 0, # How many units of padding should there be between elements horizontally
                 row_padding: float = 0, # How many units of padding should there be between elements vertically
                 row_fill: bool = False, # Start filling along rows (vertically) rather than columns (horizontally)
                 flip_column_order: bool = False, # Start from the right rather than the left
                 flip_row_order: bool = False, # Start from the bottom rather than the top
                 uniform_columns: bool = False, # If true then every column will be the same size
                 uniform_rows: bool = False, # If true then every row will be the same size 
                 contained: bool = True, # If true then the 'free' direction will be compressed until the min-size of the grid elements is reached. # TODO: what does this mean in code???
                 *,
                 bounds: Anchors | None = None,
                 minimum: Vec2 = Vec2(),
                 priority: float = 1.0,
                 anchors: Anchors | None = None,
                 offsets: Offsets | None = None,
                 size: Vec2 | None = None,
                 position: Vec2 | None = None,
                 uid: UUID | None = None
            ) -> None:
        assert wrap > 0, f"a wrap of {wrap} is invalid for a GridElement"
        super().__init__(bounds=bounds, minimum=minimum, priority=priority, anchors=anchors, offsets=offsets, size=size, position=position, uid=uid)
        self._wrap: int = max(1, wrap)
        self._count: int = count
        self._col_padding: float = column_padding
        self._row_padding: float = row_padding
        self._row_fill: bool = row_fill
        self._flip_col: bool = flip_column_order
        self._flip_row: bool = flip_row_order
        self._uniform_col: bool = uniform_columns  # TODO: impl
        self._uniform_row: bool = uniform_rows  # TODO: impl
        self._contained: bool = contained  # TODO: figure out what to do when not contained

    def __recompute_layout__(self):
        if not self._children:
            return

        rect = self._rect
        count = self._count if self._count > 0 else len(self._children)
        wrap = self._wrap
        off = ceil(count / wrap)
        row_fill = self._row_fill

        row_pad = self._row_padding
        col_pad = self._col_padding

        row_flip = self._flip_row
        col_flip = self._flip_col

        if row_fill:
            row_size = (rect.height - row_pad * (wrap - 1)) / wrap
            col_size = (rect.width - col_pad * (off - 1)) / off  # TODO: figure out what to do when not contained (largest min size maybe?)
        else:
            col_size = (rect.width - col_pad * (wrap - 1)) / wrap
            row_size = (rect.height - row_pad * (off - 1)) / off  # TODO: figure out what to do when not contained (largest min size maybe?)

        for idx, child in enumerate(self._children):
            idx = idx % count # Do the item looping if count > 0
            a_idx = idx % wrap
            b_idx = idx // wrap

            if row_fill:
                row = a_idx * (row_size + row_pad)
                col = b_idx * (col_size + col_pad)
            else:
                row = b_idx * (row_size + row_pad)
                col = a_idx * (col_size + col_pad)

            if row_flip:
                b = rect.bottom + row
                t = b + row_size
            else:
                t = rect.top - row
                b = t - row_size

            if col_flip:
                r = rect.right - col
                l = r - col_size
            else:
                l = rect.left + col
                r = l + col_size

            child.set_bounds(LRBT(l, r, b, t))

    def __add_to_tree__(self, tree: Tree | None, depth: int):
        pass

    def __remove_from_tree__(self):
        pass

    def __add_child__(self, child: Element):
        pass

    def __remove_child__(self, child: Element):
        pass

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def __move_child__(self, child: Element, idx: int):
        pass
    


# -- RENDER ELEMENTS --

class TextureElement(Element):

    def __init__(self,
                 path: str, # TODO: Make skinnable?
                 x_anchor: AxisAnchor = AxisAnchor.CENTER,
                 y_anchor: AxisAnchor = AxisAnchor.CENTER,
                 fit: FrameFit = FrameFit.STRETCH,
                 angle: float = 0.0,
                 # TODO: Allow for pixelated control
                 *,
                 bounds: Anchors | None = None,
                 minimum: Vec2 = Vec2(),
                 priority: float = 1.0,
                 anchors: Anchors | None = None,
                 offsets: Offsets | None = None,
                 size: Vec2 | None = None,
                 position: Vec2 | None = None,
                 uid: UUID | None = None
            ) -> None:
        super().__init__(bounds=bounds, minimum=minimum, priority=priority, anchors=anchors, offsets=offsets, size=size, position=position, uid=uid)

        self._texture = load_texture(path)

        self._x_anchor: AxisAnchor = x_anchor
        self._y_anchor: AxisAnchor = y_anchor
        self._fit: FrameFit = fit
        self._angle: float = angle

        self._sprite = Sprite(self._texture, 1.0)

    def __recompute_layout__(self):
        rect = self._rect
        for child in self._children:
            child.set_bounds(rect)

        width, height = self._rect.size
        match self._fit:
            case FrameFit.FIXED:
                width, height = self._texture.size
            case FrameFit.STRETCH:
                width, height = rect.size
            case FrameFit.WIDTH:
                aspect = self._texture.height / self._texture.width
                width, height = rect.width, rect.width * aspect
            case FrameFit.HEIGHT:
                aspect = self._texture.width / self._texture.height
                width, height = rect.height * aspect, rect.height
            case FrameFit.MIN:
                aspect = self._texture.width / self._texture.height
                if height * aspect < width:
                    width = height * aspect 
                else:
                    height = width / aspect
            case FrameFit.MAX:
                aspect = self._texture.width / self._texture.height
                if width < height * aspect:
                    width = height * aspect
                else:
                    height = width/ aspect
        
        x = rect.x
        match self._x_anchor:
            case AxisAnchor.LEFT:
                x = rect.left + width / 2.0
            case AxisAnchor.CENTER:
                x = rect.x
            case AxisAnchor.RIGHT:
                x = rect.right - height / 2.0

        y = rect.y
        match self._y_anchor:
            case AxisAnchor.TOP:
                y = rect.top - height / 2.0
            case AxisAnchor.CENTER:
                y = rect.y
            case AxisAnchor.BOTTOM:
                y = rect.bottom + height / 2.0

        self._sprite.position = (x, y)
        self._sprite.depth = self._depth + self._depth_offset
        self._sprite.size = (width, height)
            

    def __add_to_tree__(self, tree: Tree | None, depth: int):
        if tree is None:
            return

        tree.get_renderable(BuiltInRenderable.SPRITE).add(self._sprite)

    def __remove_from_tree__(self):
        if self._tree is not None:
            self._tree.get_renderable(BuiltInRenderable.SPRITE).remove(self._sprite)

    def __add_child__(self, child: Element):
        pass

    def __remove_child__(self, child: Element):
        pass

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def __move_child__(self, child: Element, idx: int):
        pass


class LabelElement(Element):
    X_ANCHOR_MAPPING: dict[AxisAnchor, Literal["left", "center", "right"]] = {AxisAnchor.LEFT : "left", AxisAnchor.CENTER : "center", AxisAnchor.RIGHT : "right"}
    Y_ANCHOR_MAPPING: dict[AxisAnchor, Literal["bottom", "center", "top"]] = {AxisAnchor.BOTTOM : "bottom", AxisAnchor.CENTER : "center", AxisAnchor.TOP : "top"} # TODO: Add Baseline as an option somehow

    def __init__(self,
                 text: str,
                 font: str | tuple[str, ...] = ("calibri", "arial"),
                 color: RGBOrA255 = color.WHITE,
                 font_size: float = 12.0,
                 x_anchor: AxisAnchor = AxisAnchor.CENTER,
                 y_anchor: AxisAnchor = AxisAnchor.CENTER,
                 align: AxisAnchor = AxisAnchor.CENTER,
                 multiline: bool = True,
                 # TODO: font styling (bold, italics)
                 *,
                 bounds: Anchors | None = None,
                 minimum: Vec2 = Vec2(),
                 priority: float = 1.0,
                 anchors: Anchors | None = None,
                 offsets: Offsets | None = None,
                 size: Vec2 | None = None,
                 position: Vec2 | None = None,
                 uid: UUID | None = None
            ) -> None:
        super().__init__(bounds=bounds, minimum=minimum, priority=priority, anchors=anchors, offsets=offsets, size=size, position=position, uid=uid)
        self._text = text

        self._font = font
        self._color = color
        self._font_size = font_size
        self._x_anchor = x_anchor
        self._y_anchor = y_anchor
        self._align = align
        self._multiline = multiline
        
        self._label = Text(text, 0.0, 0.0, font_size=font_size, font_name=font, color=color, anchor_x="center", anchor_y="center")

    def __recompute_layout__(self):
        rect = self._rect
        for child in self._children:
            child.set_bounds(rect)

        if self._text != self._label.text:
            self._label.text = self._text

        self._label.width = rect.width # type: ignore
        self._label.height = rect.height # type: ignore
        self._label.align = LabelElement.X_ANCHOR_MAPPING[self._align]
        self._label.multiline = self._multiline

        x = rect.x
        match (self._x_anchor, self._align):
            case AxisAnchor.LEFT, AxisAnchor.LEFT:
                x = rect.x
            case AxisAnchor.LEFT, AxisAnchor.CENTER:
                x = rect.left + self._label.content_width / 2.0
            case AxisAnchor.LEFT, AxisAnchor.RIGHT:
                x = rect.x - rect.width + self._label.content_width
            case AxisAnchor.CENTER, AxisAnchor.LEFT:
                x = rect.right - self._label.content_width / 2.0
            case AxisAnchor.CENTER, AxisAnchor.CENTER:
                x = rect.x
            case AxisAnchor.CENTER, AxisAnchor.RIGHT:
                x = rect.left + self._label.content_width / 2.0
            case AxisAnchor.RIGHT, AxisAnchor.LEFT:
                x = rect.x + rect.width - self._label.content_width
            case AxisAnchor.RIGHT, AxisAnchor.CENTER:
                x = rect.right - self._label.content_width / 2.0
            case AxisAnchor.RIGHT, AxisAnchor.RIGHT:
                x = rect.x

        y = rect.y
        match self._y_anchor:
            case AxisAnchor.TOP:
                y = rect.y
            case AxisAnchor.CENTER:
                y = rect.bottom + self._label.content_height / 2.0
            case AxisAnchor.BOTTOM:
                y = rect.y - rect.height + self._label.content_height

        self._label.position = (x, y)
        self._label.z = self._depth + self._depth_offset

        # self._label.anchor_x = LabelElement.X_ANCHOR_MAPPING[self._x_anchor]
        # self._label.anchor_y = LabelElement.Y_ANCHOR_MAPPING[self._y_anchor]


    def __add_to_tree__(self, tree: Tree | None, depth: int):
        if tree is None:
            return
        
        tree.get_renderable(BuiltInRenderable.TEXT).add(self._label)

    def __remove_from_tree__(self):
        if self._tree is None:
            return
        
        self._tree.get_renderable(BuiltInRenderable.TEXT).remove(self._label)

    def __add_child__(self, child: Element):
        pass

    def __remove_child__(self, child: Element):
        pass

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def __move_child__(self, child: Element, idx: int):
        pass


class StyleBoxElement(Element):

    def __init__(self,
                 corner_radius: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
                 margins: Offsets = Offsets(),
                 border: Offsets = Offsets(),
                 texture: str | None = None,
                 color: RGBOrA255 = color.WHITE,
                 border_color: RGBOrA255 = color.WHITE,
                 gradient: bool = False,
                 border_inwards: bool = False,
                 resolution: int = 12,
                 *,
                 bounds: Anchors | None = None,
                 minimum: Vec2 = Vec2(),
                 priority: float = 1.0,
                 anchors: Anchors | None = None,
                 offsets: Offsets | None = None,
                 size: Vec2 | None = None,
                 position: Vec2 | None = None,
                 uid: UUID | None = None
            ) -> None:
        super().__init__(bounds=bounds, minimum=minimum, priority=priority, anchors=anchors, offsets=offsets, size=size, position=position, uid=uid)
        self._corners = corner_radius
        self._margins = margins # TODO
        self._border = border
        self._texture = None if texture is None else load_texture(texture)
        self._color: RGBA255 = color if len(color) == 4 else (*color, 255)
        self._border_color: RGBA255 = border_color if len(border_color) == 4 else (*border_color, 255)
        self._gradient = gradient
        self._border_inwards = border_inwards

        self._box = StyleBox(self.rect, self._corners, self._border, self._color, self._border_color, gradient, border_inwards, resolution)

    # TODO: rect properties with stale markers.

    def __recompute_layout__(self):
        rect = self._rect
        for child in self._children:
            child.set_bounds(rect)

        if self._box.index_array is None or self._box._rect == self._rect:
            return
        
        self._box.update_rect(self.rect)

    def __add_to_tree__(self, tree: Tree | None, depth: int):
        if tree is None:
            return
        
        tree.get_renderable(BuiltInRenderable.STYLE).add(self._box)

    def __remove_from_tree__(self):
        if self._tree is None:
            return
        
        self._tree.get_renderable(BuiltInRenderable.STYLE).remove(self._box)

    def __add_child__(self, child: Element):
        pass

    def __remove_child__(self, child: Element):
        pass

    def __insert_child__(self, child: Element, idx: int):
        self.__add_child__(child)

    def __move_child__(self, child: Element, idx: int):
        pass

    def __on_cursor_enter__(self, event: CursorMotionEvent):
        pass
    
    def __on_cursor_exit__(self, event: CursorMotionEvent):
        pass

    def __on_cursor_motion__(self, event: CursorMotionEvent):
        pass

    def __on_action_input__(self, event: ActionInputEvent):
        pass

    def __on_axis_changed__(self, event: AxisChangeEvent):
        pass

    def __on_custom_event__(self, event: MintEvent):
        pass
