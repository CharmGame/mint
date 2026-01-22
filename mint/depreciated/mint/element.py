from uuid import UUID

from .compose import Composable


class Element(Composable):

    def __init__(self, layout, content, uid: UUID | None = None):
        Composable.__init__(self, None, uid)  # Elements must be compsed (for now)

        self._layout: object | None = layout
        self._content: object | None = content
