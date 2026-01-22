from __future__ import annotations
from uuid import UUID, uuid4
from typing import Generator
from contextlib import contextmanager
from weakref import WeakSet


class Composable:

    def __init__(self, parent: Composable | None = None, uid: UUID | None = None) -> None:
        self.uid: UUID = uid or uuid4()
        self._parent: Composable | None = None
        self._children: list[Composable] = []
        self._pending_children: list[Composable] = []

        if parent is not None:
            parent.compose_child(self)

    @property
    def parent(self) -> Composable | None:
        return self._parent

    @property
    def children(self) -> tuple[Composable, ...]:
        return tuple(self._children)

    def _attach(self, parent: Composable) -> None:
        self._parent = parent

    def _dettach(self) -> None:
        self._parent = None

    def compose_child(self, child: Composable) -> None:
        # Add a child that was returned from composing.
        # This child will be process when layouting.
        self._pending_children.append(child)

    def __enter__(self):
        Tree.get_tree()._composition_stacks[-1].append(self)

    def __exit__(self, typ, exc, tb):
        stack = Tree.get_tree()._composition_stacks[-1]
        composed = stack.pop()
        if stack:
            stack[-1].compose_child(composed)
        else:
            Tree.get_tree()._composition_list[-1].append(composed)

    def compose(self) -> Generator[Composable, None, None]:
        yield from ()

    def _compose(self) -> None:
        children = [*self._pending_children, *compose(self)]
        self._pending_children.clear()
        if children:
            Tree.get_tree()._register(self, *children)

    def __hash__(self) -> int:
        return hash(self.uid)

    def __eq__(self, value: Composable) -> bool:
        return value.uid == self.uid

    def __str__(self) -> str:
        return self.__class__.__name__


class Tree:
    active_tree: Tree | None = None

    @staticmethod
    def get_tree() -> Tree:
        if Tree.active_tree is None:
            raise ValueError("No tree is currently active")
        return Tree.active_tree

    def __init__(self) -> None:
        self._composition_stacks: list[list[Composable]] = []
        self._composition_list: list[list[Composable]] = []

        self._registry: WeakSet[Composable] = WeakSet()
        self._root: Composable | None = None

    @contextmanager
    def context(self) -> Generator[None, None, None]:
        tree = Tree.active_tree
        Tree.active_tree = self
        try:
            yield
        finally:
            Tree.active_tree = tree

    def mount(self, composable: Composable) -> None:
        if self._root is not None:
            raise ValueError('Cannot mount to a tree that already has a root')
        self._root = composable
        self._registry.add(self._root)

        # Todo: link events (wait to resolve when tree is active?)
        self._compose(composable)

    def _compose(self, composable: Composable) -> None:
        composable._compose()
        for child in composable._children:
            self._compose(child)

    def _register(self, parent: Composable, *children: Composable) -> list[Composable]:
        if not children:
            return []

        for child in children:
            # Todo: Validate isinstance of Composable
            if child not in self._registry:
                self._register_child(parent, child)
                if child._children:
                    self._register(child, *child._children)
        return list(children)

    def _register_child(self, parent: Composable, child: Composable) -> None:
        if child not in self._registry:
            parent._children.append(child)
            self._registry.add(child)
            child._attach(parent)

            # Todo: link events (wait to resolve when tree is active?)

    def __str__(self) -> str:
        def line(comp: Composable, depth: int = 0) -> str:
            return (
                f"{"|-"*depth}{comp}\n"
                f"{"".join(line(child, depth + 1) for child in comp._children)}"
            )
        if self._root is None:
            return "Unmounted Tree"
        return line(self._root, 0)


def compose(composable: Composable) -> list[Composable]:
    """
    compose is heavily inspired by the Textual compose functionality.

    Args:
        composable: _description_
    """
    results: list[Composable] = []
    stack: list[Composable] = []
    composed: list[Composable] = []

    tree = Tree.get_tree()
    tree._composition_stacks.append(stack)
    tree._composition_list.append(composed)

    iter_compose = iter(composable.compose())
    is_generator = hasattr(iter_compose, "throw")
    try:
        while True:
            try:
                child = next(iter_compose)
            except StopIteration:
                break

            # Todo: validate element is Composable
            # Todo: validate element is initialised properly (Do we need to?)

            if composed:
                results.extend(composed)
                composed.clear()
            if stack:
                try:
                    stack[-1].compose_child(child)
                except Exception as e:
                    if is_generator:
                        # So the error is raised inside the generator
                        # This will generate a more sensible traceback for the dev
                        iter_compose.throw(e)  # type: ignore
                    else:
                        raise e from e
            else:
                results.append(child)
        if composed:
            results.extend(composed)
            composed.clear()

    finally:
        Tree.get_tree()._composition_stacks.pop(-1)
        # Even if composing fails we have to clear the Tree so it can continue functioning
        # Todo
        pass

    return results
