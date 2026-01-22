class Layout:

    def layout_horizontal(self, element) -> float:
        """
        Compute how much width the element's children require
        and consequently how wide it must be.
        """
        pass

    def compress_width(self, element) -> float:
        """
        Take the horizontal layout and compress or grow it to account for sizing
        requirements
        """
        pass

    def layout_wrapping(self, element) -> float:
        """
        Taking the final width of the element adjust the minimum height to ensure
        wrapping is done properly.
        """
        pass

    def layout_vertical(self, element) -> float:
        """
        Compute how much height the element's children require
        and consequently how tall it must be.
        """
        pass

    def compress_height(self, element) -> float:
        """
        Take the vertical layout and compress or grow it to account for sizing
        requirements.
        """
        pass

    def layout_position(self, element) -> float:
        """
        Place the element's children based on their size.
        """
        pass


class Overlay(Layout):
    """
    Stack all children ontop of each other.
    """
    pass


class Array(Layout):
    """
    Align every child in a row or column, using their minimum and maximum sizes plus
    priority to assign width/heights.
    """
    pass


class Grid(Layout):
    """
    Align every child to a grid of fixed or dynamic width and heights.
    """
    pass


class Anchor(Layout):
    """
    Anchor the children to a sub region of the parent.
    """
    pass
