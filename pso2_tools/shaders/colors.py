import bpy

from .. import classes, colors
from . import builder

_COLOR_GROUP_COLS = 6


@classes.register
class ShaderNodePso2Colorchannels(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Colorchannels"
    bl_label = "PSO2 Colors"
    bl_icon = "NONE"

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.bl_label, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self):
        tree = builder.NodeTreeBuilder(
            bpy.data.node_groups.new(self.bl_label, "ShaderNodeTree")
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

            color = tree.add_node("ShaderNodeAttribute", (x, y), name=channel.name)
            color.attribute_type = "VIEW_LAYER"
            color.attribute_name = channel.custom_property_name

            tree.new_output("NodeSocketColor", color.label, parent=panel)
            tree.add_link(color.outputs[0], output.inputs[index])

        return tree.tree
