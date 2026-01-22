from typing import Protocol

from arcade import SpriteList, Sprite, Text
from pyglet.graphics import Batch

from charm.lib.mint.core import Renderable, BuiltInRenderable, Mint
from charm.lib.mint.implementations.arcade_stylebox import StyleBox, StyleBoxRenderer


class SpriteRenderable(Renderable):

    def __init__(self) -> None:
        self._sprite_list: SpriteList[Sprite] = SpriteList(capacity=1024)

    def add(self, sprite: Sprite):
        self._sprite_list.append(sprite)

    def remove(self, sprite: Sprite):
        self._sprite_list.remove(sprite)

    def draw(self) -> bool | None:
        self._sprite_list.draw()

    def is_empty(self) -> bool:
        return len(self._sprite_list) == 0

    def is_full(self) -> bool:
        return False

    def clear(self) -> None:
        self._sprite_list.clear()


class TextRenderbale(Renderable):

    def __init__(self) -> None:
        self._batch: Batch = Batch()

    def add(self, text: Text):
        text.batch = self._batch

    def remove(self, text: Text):
        text.batch = None

    def draw(self) -> bool | None:
        self._batch.draw()

    def is_empty(self) -> bool:
        return False

    def is_full(self) -> bool:
        return False

    def clear(self) -> None:
        # seems leaky????
        self._batch = Batch()

class Batchable(Protocol):
    batch: Batch | None

class BatchRenderable(Renderable):

    def __init__(self) -> None:
        self._batch: Batch = Batch()

    def add(self, item: Batchable) -> None:
        item.batch = self._batch

    def remove(self, item: Batchable) -> None:
        item.batch = None

    def draw(self) -> bool | None:
        self._batch.draw()

    def is_empty(self) -> bool:
        return False

    def is_full(self) -> bool:
        return False

    def clear(self) -> None:
        # seems leaky????
        self._batch = Batch()


class StyleRenderable(Renderable):

    def __init__(self) -> None:
        self.renderer = StyleBoxRenderer()
        self.renderer.prep_buffers()

    def add(self, item: StyleBox):
        self.renderer.add(item)

    def remove(self, item: StyleBox):
        self.renderer.remove(item)

    def draw(self) -> bool | None:
        self.renderer.draw()

    def is_empty(self) -> bool:
        return self.renderer._max_tri == 0

    def is_full(self) -> bool:
        return self.renderer._max_tri >= self.renderer._slots.qsize()

    def clear(self) -> None:
        self.renderer.clear_buffers()

class MeshRenderable(Renderable):
    pass


def setup_arcade() -> None:
    Mint.register_renderable(BuiltInRenderable.SPRITE, SpriteRenderable)
    Mint.register_renderable(BuiltInRenderable.TEXT, TextRenderbale)
    Mint.register_renderable(BuiltInRenderable.BATCH, BatchRenderable)
    Mint.register_renderable(BuiltInRenderable.STYLE, StyleRenderable)
    Mint.register_renderable(BuiltInRenderable.MESH, MeshRenderable)
