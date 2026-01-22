from .core import Element

from arcade import draw_rect_outline, draw_point

def debug_draw_element(element: Element, *, waterfall: bool = True, bounds: bool = False, rect: bool = True, anchors: bool = True):
    if element._has_changed_layout:
        element.recompute_layout(waterfall=True)

    if bounds and element.bounds is not None:
        draw_rect_outline(element.bounds, (255, 0, 0), 2)

    if rect:
        draw_rect_outline(element.rect, (0, 255, 0), 2)

    if anchors:
        if element._bounds is None:
            left = right = bottom = top = 0.0
        else:
            left, bottom = element._bounds.uv_to_position(element._anchors.bottom_left)
            right, top = element._bounds.uv_to_position(element._anchors.top_right)

        draw_point(left, bottom, (0, 0, 255), 4)
        draw_point(left, top, (0, 0, 255), 4)
        draw_point(right, bottom, (0, 0, 255), 4)
        draw_point(right, top, (0, 0, 255), 4)

    if waterfall:
        for child in element._children:
            debug_draw_element(child, waterfall=waterfall, bounds=bounds, rect=rect, anchors=anchors)