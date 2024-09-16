from .. import classes, colors
from . import builder, group

_COLOR_GROUP_COLS = 6


@classes.register
class ShaderNodePso2Colorchannels(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Colorchannels"
    bl_label = "PSO2 Colors"
    bl_icon = "NONE"

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

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

            color = tree.add_node("ShaderNodeAttribute", (x, y), name=channel.name)
            color.attribute_type = "VIEW_LAYER"
            color.attribute_name = channel.custom_property_name

            tree.new_output("NodeSocketColor", color.label, parent=panel)
            tree.add_link(color.outputs[0], output.inputs[index])
