from math import tau, cos, sin

QUARTER_ARC_RADIANS = tau / 4.0

type CornerPositions = tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]

def gen_stylebox(
        width: float,
        height: float,
        position: tuple[float, float],
        corner_radii: tuple[float, float, float, float],
        border_thickness: tuple[float, float, float, float],
        inner_colour: tuple[int, int, int, int] = (255, 255, 255, 255),
        border_colour: tuple[int, int, int, int] = (255, 255, 255, 255),
        gradient: bool = False,
        *,
        resolution: int = 12,
        inner_corner_radius_control: bool = False
    ) -> tuple[list[int], list[float], list[int]]:
    has_border = any( b > 0.0 for b in border_thickness )
    indices = generate_indices(has_border, resolution)

    if has_border:
        c = 4 * resolution
        colours: list[int] = [0] * 12 * c

        edge_color = inner_colour if gradient else border_colour
        colours[0:4*c] = [*border_colour] * c
        colours[4*c: 8*c] = [*edge_color] * c
        colours[8*c:] = [*inner_colour] * c
 
        inner_pos = position[0] + (border_thickness[0] - border_thickness[1]) * 0.5, position[1] + (border_thickness[2] - border_thickness[3]) * 0.5
        inner_width = width - border_thickness[0] - border_thickness[1]
        inner_height = height - border_thickness[2] - border_thickness[3]

        if inner_corner_radius_control:
            inner_radii = corner_radii
            outer_radii = (
                max(border_thickness[0], border_thickness[3]) + corner_radii[0], # top left
                max(border_thickness[3], border_thickness[1]) + corner_radii[1], # top right
                max(border_thickness[1], border_thickness[2]) + corner_radii[2], # bottom right
                max(border_thickness[2], border_thickness[0]) + corner_radii[3], # bottom left
            )
        else:
            inner_radii = (
                max(0.0, corner_radii[0] - max(border_thickness[0], border_thickness[3])), # top left
                max(0.0, corner_radii[1] - max(border_thickness[3], border_thickness[1])), # top right
                max(0.0, corner_radii[2] - max(border_thickness[1], border_thickness[2])), # bottom right
                max(0.0, corner_radii[3] - max(border_thickness[2], border_thickness[0])), # bottom left
            )
            outer_radii = corner_radii

        inner_positions = find_corner_positions(inner_width, inner_height, inner_pos, inner_radii)
        outer_positions = find_corner_positions(width, height, position, outer_radii)
    else:
        colours: list[int] = [*inner_colour] * 4 * resolution

        inner_positions = find_corner_positions(width, height, position, corner_radii)
        inner_radii = corner_radii

        outer_positions = None
        outer_radii = None

    vertices = generate_vertex_positions(inner_radii, inner_positions, outer_radii, outer_positions, resolution)

    return indices, vertices, colours


def find_corner_positions(width: float, height: float, position: tuple[float, float], radii: tuple[float, float, float, float]) -> CornerPositions:
    hw = width / 2.0
    hh = height / 2.0
    x, y = position
    top_left = x + radii[0] - hw, y + hh - radii[0]
    top_right = x + hw - radii[1], y + hh - radii[1]
    bottom_right = x + hw - radii[2], y + radii[2] - hh
    bottom_left = x +  radii[3] - hw, y + radii[3] - hh

    return top_left, top_right, bottom_right, bottom_left

def generate_indices(
        border: bool = False,
        resolution: int = 12
) -> list[int]:
    r2 = resolution * 2
    r3 = resolution * 3
    c = resolution * 4
    c2 = c * 2
    c3 = c * 3

    if border:
        # 3 idx per triangle, 2 triangles per point pair minus one
        # 3 idx per triangle, 2 triangles per point pair, 2 point pairs at a time
        indices = [0] * 6 * (6 * resolution - 1)

        for tri in range(resolution - 1):
            # Top Left
            indices[6 * tri] = tri
            indices[6 * tri + 1] = tri + 1
            indices[6 * tri + 2] = tri + c
            
            indices[6 * tri + 3] = tri + 1
            indices[6 * tri + 4] = tri + c + 1
            indices[6 * tri + 5] = tri + c

            # Top Right
            idx = tri + resolution
            indices[6 * idx] = idx
            indices[6 * idx + 1] = idx + 1
            indices[6 * idx + 2] = idx + c
            
            indices[6 * idx + 3] = idx + 1
            indices[6 * idx + 4] = idx + c + 1
            indices[6 * idx + 5] = idx + c

            # Bottom Right
            idx = tri + r2
            indices[6 * idx] = idx
            indices[6 * idx + 1] = idx + 1
            indices[6 * idx + 2] = idx + c
            
            indices[6 * idx + 3] = idx + 1
            indices[6 * idx + 4] = idx + c + 1
            indices[6 * idx + 5] = idx + c

            # Bottom Left
            idx = tri + r3
            indices[6 * idx] = idx
            indices[6 * idx + 1] = idx + 1
            indices[6 * idx + 2] = idx + c
            
            indices[6 * idx + 3] = idx + 1
            indices[6 * idx + 4] = idx + c + 1
            indices[6 * idx + 5] = idx + c

            # Left
            idx = tri + c
            offset = tri + c2
            indices[6 * idx] = offset
            indices[6 * idx + 1] = offset + 1
            indices[6 * idx + 2] = c3 - tri - 1

            indices[6 * idx + 3] = offset + 1
            indices[6 * idx + 4] = c3 - tri - 2
            indices[6 * idx + 5] = c3 - tri - 1

            # Right
            idx = tri + c + resolution
            offset = tri + c2 + resolution
            r_idx = tri + resolution
            indices[6 * idx] = offset
            indices[6 * idx + 1] = offset + 1
            indices[6 * idx + 2] = c3 - r_idx - 1
    
            indices[6 * idx + 3] = offset + 1
            indices[6 * idx + 4] = c3 - r_idx - 2
            indices[6 * idx + 5] = c3 - r_idx - 1

        # Top Left
        tri = resolution - 1
        indices[6 * tri] = tri
        indices[6 * tri + 1] = tri + 1
        indices[6 * tri + 2] = tri + c
        
        indices[6 * tri + 3] = tri + 1
        indices[6 * tri + 4] = tri + c + 1
        indices[6 * tri + 5] = tri + c

        # Top Right
        idx = tri + resolution
        indices[6 * idx] = idx
        indices[6 * idx + 1] = idx + 1
        indices[6 * idx + 2] = idx + c
        
        indices[6 * idx + 3] = idx + 1
        indices[6 * idx + 4] = idx + c + 1
        indices[6 * idx + 5] = idx + c

        # Bottom Right
        idx = tri + r2
        indices[6 * idx] = idx
        indices[6 * idx + 1] = idx + 1
        indices[6 * idx + 2] = idx + c
        
        indices[6 * idx + 3] = idx + 1
        indices[6 * idx + 4] = idx + c + 1
        indices[6 * idx + 5] = idx + c

        # Bottom Left
        idx = tri + r3
        indices[6 * idx] = c - 1
        indices[6 * idx + 1] = 0
        indices[6 * idx + 2] = c2 - 1
        
        indices[6 * idx + 3] = 0
        indices[6 * idx + 4] = c
        indices[6 * idx + 5] = c2 - 1

        # Left
        idx = tri + c
        offset = tri + c2
        indices[6 * idx] = offset
        indices[6 * idx + 1] = offset + 1
        indices[6 * idx + 2] = c3 - tri - 1

        indices[6 * idx + 3] = offset + 1
        indices[6 * idx + 4] = c3 - tri - 2
        indices[6 * idx + 5] = c3 - tri - 1

    else:
        indices = [0] * 6 * (2 * resolution - 1)

        for tri in range(resolution - 1):
            # Left
            indices[6 * tri] = tri
            indices[6 * tri + 1] = tri + 1
            indices[6 * tri + 2] = c - tri - 1

            indices[6 * tri + 3] = tri + 1
            indices[6 * tri + 4] = c - tri - 2
            indices[6 * tri + 5] = c - tri - 1

            # Right
            idx = resolution + tri

            indices[6 * idx] = idx
            indices[6 * idx + 1] = idx + 1
            indices[6 * idx + 2] = c - idx - 1

            indices[6 * idx + 3] = idx + 1
            indices[6 * idx + 4] = c - idx - 2
            indices[6 * idx + 5] = c - idx - 1

        # middle tri 1
        indices[6 * resolution - 6] = resolution - 1
        indices[6 * resolution - 5] = resolution
        indices[6 * resolution - 4] = 3 * resolution

        # middle tri 2
        indices[6 * resolution - 3] = resolution
        indices[6 * resolution - 2] = 3 * resolution - 1
        indices[6 * resolution - 1] = 3 * resolution

    return indices

def generate_vertex_positions(
        inner_radii: tuple[float, float, float, float],
        inner_positions: CornerPositions,
        outer_radii: tuple[float, float, float, float] | None = None,
        outer_positions: CornerPositions | None = None,
        resolution: int = 12
    ) -> list[float]:
    # Iterating in python is a slow operation so if you have a small fixed number of repetitive steps inlining is faster than doing the small loop.
    # In this case every corner has the same number of vertices and radius so its very easy to inline the corner loop.
    # If the number of vertices isn't constant that might change.
    c = resolution * 4
    c2 = 2 * c
    c3 = 3 * c

    arc_resolution = 0.0 if resolution == 1 else QUARTER_ARC_RADIANS / (resolution - 1)

    r_tl_i, r_tr_i, r_br_i, r_bl_i = inner_radii
    tl_i, tr_i, br_i, bl_i = inner_positions

    offset_tr = resolution
    offset_br = resolution * 2
    offset_bl = resolution * 3

    if outer_positions is None:
        points: list[float] = [0.0] * 3 * c


        for vertex in range(resolution):
            theta = vertex * arc_resolution 
            c = cos(theta)
            s = sin(theta)

            # Corner 1
            points[3 * vertex] = tl_i[0] - c * r_tl_i
            points[3 * vertex + 1] = tl_i[1] + s * r_tl_i

            # Corner 2
            idx = vertex + offset_tr
            points[3 * idx] = tr_i[0] + s * r_tr_i
            points[3 * idx + 1] = tr_i[1] + c * r_tr_i

            # Corner 3
            idx = vertex + offset_br
            points[3 * idx] = br_i[0] + c * r_br_i
            points[3 * idx + 1] = br_i[1] - s * r_br_i 

            # Corner 4
            idx = vertex + offset_bl
            points[3 * idx] = bl_i[0] - s * r_bl_i
            points[3 * idx + 1] = bl_i[1] - c * r_bl_i
    else:
        r_tl_o, r_tr_o, r_br_o, r_bl_o = outer_radii # type: ignore
        tl_o, tr_o, br_o, bl_o = outer_positions

        points: list[float] = [0.0] * 3 * c3

        for vertex in range(resolution):
            theta = vertex * arc_resolution
            co = cos(theta)
            si = sin(theta)

            # Corner 1
            idx = vertex

            points[3 * idx] = tl_o[0] - co * r_tl_o
            points[3 * idx + 1] = tl_o[1] + si * r_tl_o

            points[3 * (idx + c)] = points[3 * (idx + c2)] = tl_i[0] - co * r_tl_i
            points[3 * (idx + c) + 1] = points[3 * (idx + c2) + 1] = tl_i[1] + si * r_tl_i

            # Corner 2
            idx = vertex + offset_tr

            points[3 * idx] = tr_o[0] + si * r_tr_o
            points[3 * idx + 1] = tr_o[1] + co * r_tr_o

            points[3 * (idx + c)] = points[3 * (idx + c2)] = tr_i[0] + si * r_tr_i
            points[3 * (idx + c) + 1] = points[3 * (idx + c2) + 1] = tr_i[1] + co * r_tr_i

            # Corner 3
            idx = vertex + offset_br

            points[3 * idx] = br_o[0] + co * r_br_o
            points[3 * idx + 1] = br_o[1] - si * r_br_o

            points[3 * (idx + c)] = points[3 * (idx + c2)] = br_i[0] + co * r_br_i
            points[3 * (idx + c) + 1] = points[3 * (idx + c2) + 1] = br_i[1] - si * r_br_i

            # Corner 4
            idx = vertex + offset_bl

            points[3 * idx] = bl_o[0] - si * r_bl_o
            points[3 * idx + 1] = bl_o[1] - co * r_bl_o

            points[3 * (idx + c)] = points[3 * (idx + c2)] = bl_i[0] - si * r_bl_i
            points[3 * (idx + c) + 1] = points[3 * (idx + c2) + 1] = bl_i[1] - co * r_bl_i

    return points
