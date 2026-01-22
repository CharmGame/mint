from uuid import UUID

from .core import Element, Element, TextElement, TextureElement, StyleBoxElement


class StyleBox(Element[StyleBoxElement]):

    def __init__(self, data: StyleBoxElement, parent: Element | None = None, uid: UUID | None = None):
        Element[StyleBoxElement].__init__(self, data, parent, uid)


class Text(Element[TextElement]): ...


class Texture(Element[TextureElement]): ...