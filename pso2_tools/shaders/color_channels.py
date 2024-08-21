import bpy

from .. import colors
from ..preferences import get_preferences
from . import builder

_COLOR_GROUP_NAME = "PSO2 Colors"
_COLOR_GROUP_COLS = 6


def get_color_channels_node(context: bpy.types.Context) -> bpy.types.ShaderNodeTree:
    """
    Get a node group for PSO2 color channels.
    """
    if existing := bpy.data.node_groups.get(_COLOR_GROUP_NAME, None):
        return existing

    prefs = get_preferences(context)
    tree = builder.NodeTreeBuilder(
        bpy.data.node_groups.new(_COLOR_GROUP_NAME, "ShaderNodeTree")
    )

    output = tree.add_node("NodeGroupOutput", (28, 0))
    panels = {}

    for i, channel in colors.COLOR_CHANNELS.items():
        try:
            panel = panels[channel.group]
        except KeyError:
            panel = tree.tree.interface.new_panel(
                name=channel.group, default_closed=True
            )
            panels[channel.group] = panel

        index = i.value - 1
        x = (index % _COLOR_GROUP_COLS) * 4
        y = (index // _COLOR_GROUP_COLS) * -4

        color = tree.add_node("ShaderNodeRGB", (x, y))
        color.label = channel.name
        color.outputs[0].default_value = getattr(prefs, channel.prop)

        tree.new_output("NodeSocketColor", color.label, parent=panel)
        tree.add_link(color.outputs[0], output.inputs[index])

    return tree.tree
