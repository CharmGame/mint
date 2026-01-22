class Content:

    def wrap_content(self, width: float) -> float:
        """
        Taking the width given by the layouting algorithm, provide a minimum height.
        """
        pass

    def update_content(self) -> None:
        pass

    def attach(self) -> None:
        pass

    def detatch(self) -> None:
        pass


class StyleBox(Content):
    pass


class Image(Content):
    pass


class Text(Content):
    pass


class Blur(Content):
    pass
