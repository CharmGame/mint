from random import randint
import arcade
from arcade.draw import arc
import mint.mint as mint

def button(text: str, on_click = None):
    with mint.Element(id=f"button {text}", padding=mint.Padding(10, 10, 10, 10)):
        yield mint.Element(content=mint.Text(text), sizing=mint.Sizing(mint.Fixed(100), mint.Fixed(20)))

def compose():
    with mint.Element(layout=mint.Array(gutter=50.0, x = mint.Alignment.CENTER), padding=mint.Padding(30.0, 30.0, 30.0, 30.0), sizing=mint.Sizing(mint.Grow(), mint.Grow())):
        yield mint.Element(id="childless", sizing=mint.Sizing(mint.Grow(), mint.Grow()))
        with mint.Element(layout=mint.Array(vertical=True, gutter=20.0), padding=mint.Padding(5.0, 5.0, 5.0, 5.0)):
            yield from button("play")
            yield from button("settings")
            yield from button("exit")

# TODO: for dx make that not have to be a dimension (Sequence?)
tree = mint.Tree((1280, 720))

tree.compose(compose)
for element in tree._element_map.values():
    print(element.id)
tree.print_tree()

commands = tree._render_commands

window = arcade.Window()

colors: dict[str, arcade.types.RGBA255] = {
    "__MintRoot__rect__": (0, 0, 0, 0)
}

print("\n".join(str(c) for c in commands))

def on_draw():
    window.clear
    for command in commands:
        match command:
            case mint.RenderTextCommand():
                arcade.draw_text(command.text, command.anchor.x, command.anchor.y)
            case mint.RenderRectCommand():
                if command.id not in colors:
                    colors[command.id] = (randint(0, 255), randint(0, 255), randint(0, 255), 255)
                color = colors[command.id]
                arcade.draw_lbwh_rectangle_filled(command.region.left, command.region.bottom, command.region.width, command.region.height, color)

window.on_draw = on_draw

window.run()