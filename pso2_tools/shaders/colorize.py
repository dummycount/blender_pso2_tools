from .. import classes
from . import builder, group


@classes.register
class ShaderNodePso2Colorize(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Colorize"
    bl_label = "PSO2 Colorize"
    bl_icon = "NONE"

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

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

        mask_rgb = tree.add_node("ShaderNodeSeparateColor", name="Mask RGB")
        mask_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Mask RGB"], mask_rgb.inputs["Color"])

        color1 = tree.add_node("ShaderNodeMix", name="Color 1")
        color1.data_type = "RGBA"
        color1.blend_type = "MIX"
        color1.clamp_factor = True

        color2 = tree.add_node("ShaderNodeMix", name="Color 2")
        color2.data_type = "RGBA"
        color2.blend_type = "MIX"
        color2.clamp_factor = True

        color3 = tree.add_node("ShaderNodeMix", name="Color 3")
        color3.data_type = "RGBA"
        color3.blend_type = "MIX"
        color3.clamp_factor = True

        color4 = tree.add_node("ShaderNodeMix", name="Color 4")
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
