import logging

from charm.core.digiview import DigiView, shows_errors
from charm.core.keymap import KeyMap

from charm.lib.mint import Tree, Element, AnchorPresets, Offsets, AxisAnchor, FrameFit
from charm.lib.mint.elements import TextureElement, LabelElement, GridElement, StyleBoxElement, Offsets, ListElement
from charm.lib.mint.debug import debug_draw_element
from charm.lib.mint.implementations.arcade import setup_arcade
from arcade import LRBT, Sprite, draw_sprite, Vec2

from importlib.resources import files, path

import charm.data.images as imgs

logger = logging.getLogger("charm")

def create_list_element(string: str):
    box = StyleBoxElement((0.0, 23.0, 23.0, 0.0), anchors=LRBT(0.0, 1.0, 0.0, 1.0), minimum=Vec2(0.0, 88.0), color=(186, 162, 247), priority=0.0)
    items = ListElement(AxisAnchor.LEFT, padding=10.0)
    items.add_child(LabelElement(string, "bananaslip plus", x_anchor=AxisAnchor.RIGHT, font_size=18, color=(0, 0, 0, 255)))
    box.add_child(items)
    return box

class MintView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        setup_arcade()
        with path(imgs, "debug/menu_layout_test_blur.png") as p:
            self.deboobop = Sprite(p, 1.0, self.center_x, self.center_y)

        self.mint_tree = Tree()

        self.root = Element(bounds=self.window.rect)
        self.mint_tree.set_root(self.root)

        self.list = ListElement(vertical=True, anchors=LRBT(0.0, 0.6, 0.0, 1.0), contained=False, padding=10.0)
        self.root.add_child(self.list)

        self.list.add_children(
            (
                create_list_element('Expurgation'),
                create_list_element('Never Gonna Give You Up'),
                create_list_element('Run Around The Character Code!'),
                create_list_element('Soulless 5'),
                create_list_element('I Love Rock and Roll'),
                create_list_element('FREEDOM DRIVE')
            )
        )

        self.panel = StyleBoxElement(anchors=LRBT(2.0/3.0, 1.0, 0.0, 1.0), border=Offsets(129, 129, 0.0, 0.0), color=(0, 0, 0, 25), border_color=(0, 0, 0, 50), gradient=True, resolution=1)
        self.root.add_child(self.panel)

        self.search = StyleBoxElement(anchors=LRBT(0.0, 1.0, 1.0, 1.0), offsets=Offsets(13.0, -13.0, -51.0, -10.0), corner_radius=(20.0, 20.0, 20.0, 20.0))
        self.topic = StyleBoxElement(anchors=LRBT(0.0, 1.0, 1.0, 1.0), offsets=Offsets(25.0, -25.0, -76.0, -56.0), corner_radius=(10.0, 10.0, 10.0, 10.0), color=(0, 0, 0, 50))
        with path(imgs, "no_image_found.png") as p:
            self.album_art = TextureElement(str(p), fit=FrameFit.MIN, anchors=LRBT(0.0, 1.0, 0.5, 1.0), offsets=Offsets(0.0, 0.0, 45.0, -93.0))
        self.title = LabelElement("文字コードをかけめぐれ！🏃💨", "bananaslip plus", color=(0, 0, 0, 255), font_size=15.0, anchors=LRBT(0.0, 1.0, 0.5, 0.5), offsets=Offsets(0.0, 0.0, 0.0, 30.0))
        self.artists = LabelElement("Camellia ft. nanahira", "bananaslip plus", color=(0, 0, 0, 255), font_size=10.0, anchors=LRBT(0.0, 1.0, 0.5, 0.5), offsets=Offsets(0.0, 0.0, -26.0, -6.0))
        self.album = LabelElement("5LEEP!", "bananaslip plus", color=(0, 0, 0, 255), font_size=10.0, anchors=LRBT(0.0, 1.0, 0.5, 0.5), offsets=Offsets(0.0, 0.0, -52.0, -32.0))
        self.charter = LabelElement("from ori0ta", "bananaslip plus", color=(0, 0, 0, 255), font_size=8.0, anchors=LRBT(0.0, 1.0, 0.5, 0.5), offsets=Offsets(0.0, 0.0, -74.0, -58.0))
        self.metadata = StyleBoxElement(anchors=LRBT(0.0, 1.0, 0.0, 0.5), offsets=Offsets(31.0, -31.0, 100.0, -100.0), corner_radius=(25.0, 25.0, 25.0, 25.0), color=(0, 0, 0, 50))
        self.best = Element(anchors=LRBT(0.0, 1.0, 0.0, 0.0), offsets=Offsets(0.0, 0.0, 15.0, 75.0))

        self.panel.add_children(
            (self.search, self.topic, self.album_art, self.title, self.artists, self.album, self.charter, self.metadata, self.best)
        )

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        super().postsetup()

    @shows_errors
    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.mint_tree.update_viewport(width, height)


    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.back.pressed:
            self.go_back()

    @shows_errors
    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.wrapper.update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.wrapper.draw()
        draw_sprite(self.deboobop)

        self.mint_tree.draw()
        # debug_draw_element(self.root)

        super().postdraw()
