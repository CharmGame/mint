from charm.core.digiview import DigiView, shows_errors
from charm.core.keymap import KeyMap

from charm.lib.mint import Tree, Element, ElementData, AxisAnchor, Offsets
from charm.lib.mint.core import ArrayElement


class MintDebug2View(DigiView):

    def __init__(self, back: DigiView | None = None):
        DigiView.__init__(self, back=back)

        self.tree = Tree()

        self.root = ArrayElement(padding=Offsets(16.0, 16.0, 16.0, 16.0), child_padding=16.0, vertical=True).create()
        self.tree.set_root(self.root)

        self.root.add_child(ElementData(
            priority=2
            ).create()
        )
        self.root.add_child(ElementData(
                maximum_height=130,
                horizontal_alignmnet=AxisAnchor.LEFT,
                vertical_alignment=AxisAnchor.TOP
            ).create()
        )
        self.root.add_child(ElementData(
            priority=2
            ).create()
        )

    @shows_errors
    def on_resize(self, width: int, height: int) -> None:
        self.tree.update_viewport(width, height)

    @shows_errors
    def on_draw(self) -> None:
        self.clear()
        self.predraw()
        self.tree.draw()
        self.postdraw()

