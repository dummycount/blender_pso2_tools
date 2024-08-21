import bpy

from .. import classes
from . import builder


@classes.register
class ShaderNodePso2MixTexture(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2MixTexture"
    bl_label = "PSO2 Mix Texture"
    bl_icon = "NONE"

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.name, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self):
        tree = builder.NodeTreeBuilder(
            bpy.data.node_groups.new(self.name, "ShaderNodeTree")
        )

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketFloat", "Factor")
        tree.new_input("NodeSocketColor", "Color 1")
        tree.new_input("NodeSocketFloat", "Alpha 1")
        tree.new_input("NodeSocketColor", "Color 2")
        tree.new_input("NodeSocketFloat", "Alpha 2")

        tree.new_output("NodeSocketColor", "Color")
        tree.new_output("NodeSocketColor", "Alpha")

        color = tree.add_node("ShaderNodeMix")
        color.name = "Color"
        color.label = color.name
        color.data_type = "RGBA"
        color.blend_type = "MIX"
        color.clamp_factor = True

        alpha = tree.add_node("ShaderNodeMix")
        alpha.name = "Color 2"
        alpha.label = alpha.name
        alpha.data_type = "FLOAT"
        alpha.blend_type = "MIX"
        alpha.clamp_factor = True

        tree.add_link(group_inputs.outputs["Factor"], color.inputs["Factor"])
        tree.add_link(group_inputs.outputs["Color 1"], color.inputs["A"])
        tree.add_link(group_inputs.outputs["Color 2"], color.inputs["B"])

        tree.add_link(group_inputs.outputs["Factor"], alpha.inputs["Factor"])
        tree.add_link(group_inputs.outputs["Alpha 1"], alpha.inputs["A"])
        tree.add_link(group_inputs.outputs["Alpha 2"], alpha.inputs["B"])

        tree.add_link(color.outputs["Result"], group_outputs.inputs["Color"])
        tree.add_link(alpha.outputs["Result"], group_outputs.inputs["Alpha"])

        return tree.tree
