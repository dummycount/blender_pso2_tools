import bpy

from .. import classes
from ..colors import ColorId, ColorMapping
from . import builder, group


@classes.register
class ShaderNodePso2Colorize(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Colorize"
    bl_label = "PSO2 Colorize"
    bl_icon = "NONE"

    def _set_channel_used(self, channel: int, used: bool):
        self.input(bpy.types.NodeSocketBool, f"Use Color {channel}").default_value = (
            used
        )

    def set_colors_used(self, colors: ColorMapping | list[int]):
        if isinstance(colors, ColorMapping):
            self._set_channel_used(1, colors.red != ColorId.UNUSED)
            self._set_channel_used(2, colors.green != ColorId.UNUSED)
            self._set_channel_used(3, colors.blue != ColorId.UNUSED)
            self._set_channel_used(4, colors.alpha != ColorId.UNUSED)
        else:
            self._set_channel_used(1, 1 in colors)
            self._set_channel_used(2, 2 in colors)
            self._set_channel_used(3, 3 in colors)
            self._set_channel_used(4, 4 in colors)

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketColor", "Input")
        tree.new_input("NodeSocketColor", "Mask RGB")
        tree.new_input("NodeSocketFloat", "Mask A")
        tree.new_input("NodeSocketBool", "Use Color 1")
        tree.new_input("NodeSocketBool", "Use Color 2")
        tree.new_input("NodeSocketBool", "Use Color 3")
        tree.new_input("NodeSocketBool", "Use Color 4")
        tree.new_input("NodeSocketColor", "Color 1")
        tree.new_input("NodeSocketColor", "Color 2")
        tree.new_input("NodeSocketColor", "Color 3")
        tree.new_input("NodeSocketColor", "Color 4")

        tree.new_output("NodeSocketColor", "Result")

        mask_rgb = tree.add_node("ShaderNodeSeparateColor", name="Mask RGB")
        mask_rgb.mode = "RGB"

        mask_rgb_used = tree.add_node("ShaderNodeCombineXYZ", name="Combine RGB Used")

        tree.add_link(group_inputs.outputs["Use Color 1"], mask_rgb_used.inputs["X"])
        tree.add_link(group_inputs.outputs["Use Color 2"], mask_rgb_used.inputs["Y"])
        tree.add_link(group_inputs.outputs["Use Color 3"], mask_rgb_used.inputs["Z"])

        rgb_used = tree.add_node("ShaderNodeVectorMath", name="Mask RGB Used")
        rgb_used.operation = "MULTIPLY"

        alpha_used = tree.add_node("ShaderNodeMath", name="Mask A Used")
        alpha_used.operation = "MULTIPLY"

        tree.add_link(group_inputs.outputs["Mask RGB"], rgb_used.inputs[0])
        tree.add_link(mask_rgb_used.outputs["Vector"], rgb_used.inputs[1])

        tree.add_link(group_inputs.outputs["Mask A"], alpha_used.inputs[0])
        tree.add_link(group_inputs.outputs["Use Color 4"], alpha_used.inputs[1])

        tree.add_link(rgb_used.outputs[0], mask_rgb.inputs["Color"])

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
        tree.add_link(alpha_used.outputs[0], color4.inputs["Factor"])

        tree.add_link(color4.outputs["Result"], group_outputs.inputs["Result"])
