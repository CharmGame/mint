from __future__ import annotations

from array import array
from queue import PriorityQueue
from heapq import heapify, nsmallest
from uuid import UUID, uuid4

from charm.data import get_shader_path
from charm.lib.mint.rendering.style_box import gen_stylebox, generate_vertex_positions, find_corner_positions
from arcade import load_texture, Text, Rect, XYWH, Vec2, get_window, ArcadeContext
import arcade.gl as gl
from arcade.types import RGBA255


class StyleBox:

    def __init__(
            self,
            rect: Rect,
            corners: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
            borders: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
            inner_colour: RGBA255 = (255, 255, 255, 255),
            outer_colour: RGBA255 = (255, 255, 255, 255),
            gradient: bool = False,
            border_inwards: bool = False,
            resolution: int = 12
        ) -> None:
        self._rect: Rect = rect
        self._corner_radii: tuple[float, float, float, float] = corners
        self._border_thickness: tuple[float, float, float, float] = borders
        self._inner_color: RGBA255 = inner_colour
        self._border_color: RGBA255 = outer_colour
        self._gradient: bool = gradient
        self._inner_corner_control: bool = border_inwards
        self._depth: float = 0.0

        self._has_border = any(v > 0.0 for v in self._border_thickness)

        self._resolution: int = resolution

        self.value_count = self._resolution * (4 + 8 * self._has_border)
        self.tri_count = self._resolution * (4 + 8 * self._has_border) - 2

        self.slots: tuple[int, ...] = None
        self.renderer: StyleBoxRenderer = None
        self.idx_start: int  = -1

        self.index_array: array[int] = None
        self.vertex_array: array[float] = None
        self.colour_array: array[int] = None

    def regenerate_vertices(self) -> None:
        x, y, w, h = self._rect.xywh
        indices, vertices, colour = gen_stylebox(
            w, h, (x, y),
            self._corner_radii,
            self._border_thickness,
            self._inner_color,
            self._border_color,
            self._gradient,
            resolution=self._resolution,
            inner_corner_radius_control=self._inner_corner_control
        )

        self.index_array = array('I', indices)
        self.vertex_array = array('f', vertices)
        self.colour_array = array('B', colour)

    # TODO: move to renderer?

    def _update_vertex(self):
        if self.renderer is None or self.idx_start < 0:
            return

        indices = self.index_array
        slots = self.slots

        target_array = self.renderer._vertex_array
        source_array = self.vertex_array

        for idx in range(3 * self.tri_count):
            source = indices[idx]
            target = slots[source]

            target_array[3 * target]     = source_array[3 * source]
            target_array[3 * target + 1] = source_array[3 * source + 1]
            target_array[3 * target + 2] = source_array[3 * source + 2]

        self.renderer._vertex_stale = True

    def _update_colour(self):
        if self.renderer is None or self.idx_start < 0:
            return

        indices = self.index_array
        slots = self.slots

        target_array = self.renderer._colour_array
        source_array = self.colour_array

        for idx in range(3 * self.tri_count):
            source = indices[idx]
            target = slots[source]

            target_array[4 * target]     = source_array[4 * source]
            target_array[4 * target + 1] = source_array[4 * source + 1]
            target_array[4 * target + 2] = source_array[4 * source + 2]
            target_array[4 * target + 3] = source_array[4 * source + 3]

        self.renderer._colour_stale = True

    def _update(self):
        if self.renderer is None or self.idx_start < 0:
            return

        indices = self.index_array
        slots = self.slots

        target_colour = self.renderer._colour_array
        source_colour = self.colour_array

        target_vertex = self.renderer._vertex_array
        source_vertex = self.renderer._colour_array

        for idx in range(3 * self.tri_count):
            source = indices[idx]
            target = slots[source]

            target_vertex[3 * target]     = source_vertex[3 * source]
            target_vertex[3 * target + 1] = source_vertex[3 * source + 1]
            target_vertex[3 * target + 2] = source_vertex[3 * source + 2]

            target_colour[4 * target]     = source_colour[4 * source]
            target_colour[4 * target + 1] = source_colour[4 * source + 1]
            target_colour[4 * target + 2] = source_colour[4 * source + 2]
            target_colour[4 * target + 3] = source_colour[4 * source + 3]

        self.renderer._vertex_stale = True
        self.renderer._colour_stale = True

    def update_position(self, new_position: Vec2) -> None:
        if new_position == self._rect.center:
            return

        dx, dy = new_position - self._rect.center
        self._rect = XYWH(new_position.x, new_position.y, self._rect.width, self._rect.height)

        vertices = self.vertex_array

        for idx in range(self.value_count):
            idx = 3 * idx
            vertices[idx] = vertices[idx] + dx
            vertices[idx + 1] = vertices[idx] + dy

        self._update_vertex()

    def update_size(self, new_size: Vec2) -> None:
        self.update_rect(XYWH(self._rect.x, self._rect.y, new_size.x, new_size.y))   

    def update_rect(self, new_rect: Rect) -> None:
        self._rect = new_rect

        self.recalulate_positions()

    def recalulate_positions(self):
        x, y, w, h = self._rect.xywh
        tl, tr, br, bl = self._corner_radii
        l, r, b, t = self._border_thickness

        if self._has_border:
            inner_pos = x + (l - r) * 0.5, y + (t - b) * 0.5
            inner_width = w - l - r
            inner_height = h - b - t

            if self._inner_corner_control:
                inner_radii = self._corner_radii
                outer_radii = (
                    max(t, l) + tl, # top left
                    max(t, r) + tr, # top right
                    max(b, r) + br, # bottom right
                    max(b, l) + bl, # bottom left
                )
            else:
                inner_radii = (
                    max(0.0, tl - max(t, l)), # top left
                    max(0.0, tr - max(t, r)), # top right
                    max(0.0, br - max(b, r)), # bottom right
                    max(0.0, bl - max(b, l)), # bottom left
                )
                outer_radii = self._corner_radii

            inner_positions = find_corner_positions(inner_width, inner_height, inner_pos, inner_radii)
            outer_positions = find_corner_positions(w, h, (x, y), outer_radii)
        else:
            inner_positions = find_corner_positions(w, h, (x, y), self._corner_radii)
            inner_radii = self._corner_radii

            outer_positions = None
            outer_radii = None

        self.vertex_array = array('f', generate_vertex_positions(inner_radii, inner_positions, outer_radii, outer_positions, self._resolution))
        self._update_vertex()

    def update_corners(self, top_left: float | None = None, top_right: float | None = None, bottom_right: float | None = None, bottom_left: float | None = None):
        tl, tr, br, bl = self._corner_radii
        corners = (
            tl if top_left is None else top_left,
            tr if top_right is None else top_right,
            br if bottom_right is None else bottom_right,
            bl if bottom_left is None else bottom_left
        )

        if corners == self._corner_radii:
            return
        self._corner_radii = corners
        self.recalulate_positions()

    def update_borders(self, left: float | None = None, right: float | None = None, bottom: float | None = None, top: float | None = None):#
        l, r, b, t = self._border_thickness
        borders = (
            l if left is None else left,
            r if right is None else right,
            b if bottom is None else bottom,
            t if top is None else top
        )

        if borders == self._border_thickness:
            return
        self._border_thickness = borders
        self.recalulate_positions()

    def update_colors(self, inner: RGBA255 | None = None, border: RGBA255 | None = None):
        if self.index_array is None:
            self._inner_color = inner if inner is not None else self._inner_color
            self._border_color = border if border is not None else self._border_color
            return

        c = 4 * self._resolution
        c2 = 2 * c

        changed = False

        if inner is not None and inner != self._inner_color:
            start = c if self._gradient else c2
            count = c2 if self._gradient else c
            self.colour_array[4 * start:] = array('B', [*inner] * count)

            self._inner_color = inner

            changed = True

        if border is not None and border != self._border_color:
            count = c2 if self._gradient else c
            self.colour_array[0 : 4 * count] = array('B', [*border] * count)

            self._border_color = border

            changed = True

        if changed:
            self._update_colour()

    def update_depth(self, depth: float):
        if depth == self._depth:
            return

        self._depth = depth

        self.vertex_array[::3] = array('f', [depth] * self.value_count)
        self._update_vertex()

    def set_gradient(self, gradient: bool):
        if gradient == self._gradient:
            return

        if not self._has_border or self.index_array is None or self._inner_color == self._border_color:
            self._gradient = gradient
            return

        c = 4 * self._resolution
        c2 = 2 * c

        new_color = self._inner_color if gradient else self._border_color

        self.colour_array[4 * c: 4 * c2] = array('B', [*new_color] * c)

        self._gradient = gradient

    def set_corner_control(self, inner_corner_control: bool):
        # TODO: update vertices
        pass

    def update_resolution(self, resolution: int):
        # TODO: update vertices
        pass

class StyleBoxRenderer:
    _INDEX_STEP_SIZE = 3
    _VERTEX_STEP_SIZE = 3
    _COLOUR_STEP_SIZE = 4
    _INDEX_BYTE_SIZE = _INDEX_STEP_SIZE * 4 # 3 4 byte integers
    _VERTEX_BYTE_SIZE = _VERTEX_STEP_SIZE * 4 # 3 4 byte floats
    _COLOUR_BYTE_SIZE = _COLOUR_STEP_SIZE * 1 # 4 1 byte floats


    def __init__(self, reserve: int = 32768) -> None:
        self._initialised: bool = False
        self._reserve: int = reserve

        self._index_array: array = array('I', [0] * 3 * reserve)
        self._vertex_array: array = array('f', [.0] * 3 * reserve)
        self._colour_array: array = array('B', [0] * 4 * reserve)

        self._index_buffer: gl.Buffer = None
        self._vertex_buffer: gl.Buffer = None
        self._colour_buffer: gl.Buffer = None

        self._index_stale: bool = False
        self._vertex_stale: bool = False
        self._colour_stale: bool = False

        self._style_box_program: gl.Program = None
        self._style_box_geometry: gl.Geometry = None

        self._slots: PriorityQueue[int] = PriorityQueue()
        self._slots.queue = list(range(reserve))
        heapify(self._slots.queue)

        self._max_tri: int = 0

        self._style_boxes: list[StyleBox] = []

        self._ctx: ArcadeContext = None

    def prep_buffers(self):
        self.stale_buffers()

        if self._index_buffer != None:
            return

        self._ctx = ctx = get_window().ctx

        self._index_buffer = ctx.buffer(reserve=self._reserve * StyleBoxRenderer._INDEX_BYTE_SIZE)
        self._vertex_buffer = ctx.buffer(reserve=self._reserve * StyleBoxRenderer._VERTEX_BYTE_SIZE)
        self._colour_buffer = ctx.buffer(reserve=self._reserve * StyleBoxRenderer._COLOUR_BYTE_SIZE)

        self._style_box_program = ctx.load_program(
            vertex_shader=get_shader_path('style_vs'),
            fragment_shader=get_shader_path('style_fs')
        )

        self._style_box_geometry = ctx.geometry(
            [
                gl.BufferDescription(self._vertex_buffer, '3f', ['in_pos']),
                gl.BufferDescription(self._colour_buffer, '4f1', ['in_colour'])
            ],
            self._index_buffer, 
            gl.TRIANGLES
        )


    def stale_buffers(self):
        self._index_stale = True
        self._vertex_stale = True
        self._colour_stale = True

    def update_buffers(self):
        if self._index_stale:
            self._index_buffer.write(self._index_array.tobytes())
            self._index_stale = False

        if self._vertex_stale:
            self._vertex_buffer.write(self._vertex_array.tobytes())
            self._vertex_stale = False

        if self._colour_stale:
            self._colour_buffer.write(self._colour_array.tobytes())
            self._colour_stale = False

    def clear_buffers(self):
        for box in self._style_boxes:
            box.idx_start = -1
            box.slots = ()
            box.renderer = None
        self._style_boxes = []

        self._max_tri = 0

        self._slots.queue = list(range(self._reserve))
        heapify(self._slots.queue)

    def add(self, item: StyleBox):
        if item.index_array is None:
            item.regenerate_vertices()

        if item in self._style_boxes:
            return

        size = item.tri_count

        if size > self._slots.qsize():
            raise NotImplementedError(f'StyleBoxRenderer does not currently support resizing when out of slots.')

        item.idx_start = self._max_tri
        indices = item.slots = tuple(self._slots.get_nowait() for _ in range(item.value_count))
        targets = array('I', [0] * 3 * size)

        for idx in range(3 * size):
            source = item.index_array[idx]
            target = targets[idx] = indices[source]
            self._vertex_array[3 * target] = item.vertex_array[3 * source]
            self._vertex_array[3 * target + 1] = item.vertex_array[3 * source + 1]
            self._vertex_array[3 * target + 2] = item.vertex_array[3 * source + 2]

            self._colour_array[4 * target] = item.colour_array[4 * source]
            self._colour_array[4 * target + 1] = item.colour_array[4 * source + 1]
            self._colour_array[4 * target + 2] = item.colour_array[4 * source + 2]
            self._colour_array[4 * target + 3] = item.colour_array[4 * source + 3]

        self._index_array[3 * self._max_tri : 3 * (self._max_tri + size)] =  targets
        self._max_tri = self._max_tri + size

        self._style_boxes.append(item)
        item.renderer = self

        self.stale_buffers()

    def remove(self, item: StyleBox):
        if item not in self._style_boxes or item.idx_start < 0:
            return

        start_box = 3 * item.idx_start
        length_box = item.tri_count * 3
        end_box = start_box + length_box

        start_data = end_box
        end_data = self._max_tri * 3

        end_range = end_data - length_box

        # Move all data after indices being removed to keep data contiguous
        self._index_array[start_box:end_range] = self._index_array[start_data:end_data]
        self._max_tri -= item.tri_count

        # Free the boxes used data slots. This doesn't need to be contiguous (thanks idx array!)
        for slot in item.slots:
            self._slots.put_nowait(slot)
        item.idx_start = -1
        item.slots = ()

        self._style_boxes.remove(item)
        item.renderer = None

        self.stale_buffers()

    def update_colours(self, box: StyleBox):
        if box.slots:
            return

        for idx in range(3 * box.tri_count):
            source = box.index_array[idx]
            target = box.slots[source]

            self._colour_array[4 * target] = box.colour_array[4 * source]
            self._colour_array[4 * target + 1] = box.colour_array[4 * source + 1]
            self._colour_array[4 * target + 2] = box.colour_array[4 * source + 2]
            self._colour_array[4 * target + 3] = box.colour_array[4 * source + 3]

        self._colour_stale = True

    def update_vertices(self, box: StyleBox):
        if box.slots:
            return

        for idx in range(3 * box.tri_count):
            source = box.index_array[idx]
            target = box.slots[source]

            self._vertex_array[3 * target] = box.vertex_array[3 * source]
            self._vertex_array[3 * target + 1] = box.vertex_array[3 * source + 1]
            self._vertex_array[3 * target + 2] = box.vertex_array[3 * source + 2]

        self._vertex_stale = True

    def update_values(self, box: StyleBox):
        if box.slots:
            return

        for idx in range(3 * box.tri_count):
            source = box.index_array[idx]
            target = box.slots[source]

            self._colour_array[4 * target] = box.colour_array[4 * source]
            self._colour_array[4 * target + 1] = box.colour_array[4 * source + 1]
            self._colour_array[4 * target + 2] = box.colour_array[4 * source + 2]
            self._colour_array[4 * target + 3] = box.colour_array[4 * source + 3]

            self._vertex_array[3 * target] = box.vertex_array[3 * source]
            self._vertex_array[3 * target + 1] = box.vertex_array[3 * source + 1]
            self._vertex_array[3 * target + 2] = box.vertex_array[3 * source + 2]

        self._colour_stale = True
        self._vertex_stale = True

    def draw(self):
        self.update_buffers()
        prev_func = self._ctx.blend_func
        self._ctx.blend_func = self._ctx.BLEND_DEFAULT
        with self._ctx.enabled(self._ctx.BLEND):
            self._style_box_geometry.render(self._style_box_program, vertices=self._max_tri * 3)
        self._ctx.blend_func = prev_func



