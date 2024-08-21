import bpy

from .. import classes
from . import builder


@classes.register
class ShaderNodePso2Colorize(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Colorize"
    bl_label = "PSO2 Colorize"
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

        tree.new_input("NodeSocketColor", "Input")
        tree.new_input("NodeSocketColor", "Mask RGB")
        tree.new_input("NodeSocketFloat", "Mask A")
        tree.new_input("NodeSocketColor", "Color 1")
        tree.new_input("NodeSocketColor", "Color 2")
        tree.new_input("NodeSocketColor", "Color 3")
        tree.new_input("NodeSocketColor", "Color 4")

        tree.new_output("NodeSocketColor", "Result")

        mask_rgb = tree.add_node("ShaderNodeSeparateColor")
        mask_rgb.name = "Mask RGB"
        mask_rgb.label = mask_rgb.name
        mask_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Mask RGB"], mask_rgb.inputs["Color"])

        color1 = tree.add_node("ShaderNodeMix")
        color1.name = "Color 1"
        color1.label = color1.name
        color1.data_type = "RGBA"
        color1.blend_type = "MIX"
        color1.clamp_factor = True

        color2 = tree.add_node("ShaderNodeMix")
        color2.name = "Color 2"
        color2.label = color2.name
        color2.data_type = "RGBA"
        color2.blend_type = "MIX"
        color2.clamp_factor = True

        color3 = tree.add_node("ShaderNodeMix")
        color3.name = "Color 3"
        color3.label = color3.name
        color3.data_type = "RGBA"
        color3.blend_type = "MIX"
        color3.clamp_factor = True

        color4 = tree.add_node("ShaderNodeMix")
        color4.name = "Color 4"
        color4.label = color4.name
        color4.data_type = "RGBA"
        color4.blend_type = "MIX"
        color4.clamp_factor = True

        tree.add_link(group_inputs.outputs["Input"], color1.inputs["A"])
        tree.add_link(group_inputs.outputs["Color 1"], color1.inputs["B"])
        tree.add_link(mask_rgb.outputs["Red"], color1.inputs["Factor"])

        tree.add_link(color1.outputs["Result"], color2.inputs["A"])
        tree.add_link(group_inputs.outputs["Color 2"], color2.inputs["B"])
        tree.add_link(mask_rgb.outputs["Green"], color2.inputs["Factor"])

        tree.add_link(color2.outputs["Result"], color3.inputs["A"])
        tree.add_link(group_inputs.outputs["Color 3"], color3.inputs["B"])
        tree.add_link(mask_rgb.outputs["Blue"], color3.inputs["Factor"])

        tree.add_link(color3.outputs["Result"], color4.inputs["A"])
        tree.add_link(group_inputs.outputs["Color 4"], color4.inputs["B"])
        tree.add_link(group_inputs.outputs["Mask A"], color4.inputs["Factor"])

        tree.add_link(color4.outputs["Result"], group_outputs.inputs["Result"])

        return tree.tree
