from typing import cast

import bpy

from .. import classes
from . import builder, group


@classes.register
class ShaderNodePso2AlphaThreshold(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2AlphaThreshold"
    bl_label = "PSO2 Alpha Threshold"
    bl_icon = "NONE"

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketFloat", "Alpha")
        tree.new_input("NodeSocketFloat", "Threshold")

        tree.new_output("NodeSocketFloat", "Alpha")

        threshold = tree.add_node("ShaderNodeMath", name="Above Threshold")
        threshold.operation = "GREATER_THAN"

        disabled = tree.add_node("ShaderNodeMath", name="Disabled")
        disabled.operation = "COMPARE"
        disabled.inputs[1].default_value = 0  # type: ignore
        disabled.inputs[2].default_value = 0  # type: ignore

        mix = tree.add_node("ShaderNodeMix", name="Mix")
        mix.data_type = "FLOAT"
        mix.clamp_result = True

        tree.add_link(group_inputs.outputs["Alpha"], threshold.inputs[0])
        tree.add_link(group_inputs.outputs["Threshold"], threshold.inputs[1])

        tree.add_link(group_inputs.outputs["Threshold"], disabled.inputs[0])

        tree.add_link(disabled.outputs["Value"], mix.inputs["Factor"])
        tree.add_link(threshold.outputs["Value"], mix.inputs["A"])
        tree.add_link(group_inputs.outputs["Alpha"], mix.inputs["B"])

        tree.add_link(mix.outputs["Result"], group_outputs.inputs["Alpha"])


class ShaderNodePso2NgsBase(group.ShaderNodeCustomGroup):
    def init(self, context):
        super().init(context)

        self.input(bpy.types.NodeSocketColor, "Diffuse").default_value = (1, 0, 1, 1)
        self.input(bpy.types.NodeSocketFloat, "Alpha").default_value = 1
        self.input(bpy.types.NodeSocketFloat, "Alpha Threshold").default_value = 0
        self.input(bpy.types.NodeSocketColor, "Multi RGB").default_value = (0, 1, 1, 1)

    def draw_buttons(self, context, layout):
        layout.prop(self, "alpha_threshold")

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketColor", "Diffuse")
        tree.new_input("NodeSocketFloat", "Alpha")
        tree.new_input("NodeSocketFloat", "Alpha Threshold")
        tree.new_input("NodeSocketColor", "Multi RGB")
        tree.new_input("NodeSocketFloat", "Multi A")
        tree.new_input("NodeSocketColor", "Normal")

        tree.new_output("NodeSocketShader", "BSDF")

        bsdf = tree.add_node("ShaderNodeBsdfPrincipled")
        tree.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Normal Map ==========

        normal_map = tree.add_node("ShaderNodeNormalMap")

        tree.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        tree.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Multi Map ==========

        multi_rgb = tree.add_node("ShaderNodeSeparateColor", name="Multi Map RGB")
        multi_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Multi RGB"], multi_rgb.inputs["Color"])
        tree.add_link(multi_rgb.outputs["Red"], bsdf.inputs["Metallic"])

        # Tone down the shininess a bit to better match in game visuals
        roughness_map = tree.add_node("ShaderNodeMapRange", name="Roughness Rescale")
        roughness_map.data_type = "FLOAT"
        roughness_map.interpolation_type = "LINEAR"
        roughness_map.clamp = True
        roughness_map.inputs["To Min"].default_value = 0.2  # type: ignore
        roughness_map.inputs["To Max"].default_value = 1  # type: ignore

        tree.add_link(multi_rgb.outputs["Green"], roughness_map.inputs["Value"])
        tree.add_link(roughness_map.outputs["Result"], bsdf.inputs["Roughness"])

        # Ambient Occlusion
        # (This should really only affect ambient light, but this looks good enough)
        ao = tree.add_node("ShaderNodeMix", name="Ambient Occlusion")
        ao.data_type = "RGBA"
        ao.blend_type = "MULTIPLY"
        ao.inputs["Factor"].default_value = 1  # type: ignore

        tree.add_link(multi_rgb.outputs["Blue"], ao.inputs["B"])
        tree.add_link(ao.outputs["Result"], bsdf.inputs["Base Color"])

        # Emissive
        tree.add_link(group_inputs.outputs["Multi A"], bsdf.inputs["Emission Strength"])
        tree.add_link(group_inputs.outputs["Diffuse"], bsdf.inputs["Emission Color"])

        # ========== Base color ==========

        tree.add_link(group_inputs.outputs["Diffuse"], ao.inputs["A"])

        # ========== Alpha ==========

        alpha: ShaderNodePso2AlphaThreshold = tree.add_node(
            "ShaderNodePso2AlphaThreshold", name="Alpha"
        )  # type: ignore

        tree.add_link(group_inputs.outputs["Alpha"], alpha.inputs["Alpha"])
        tree.add_link(
            group_inputs.outputs["Alpha Threshold"], alpha.inputs["Threshold"]
        )

        tree.add_link(alpha.outputs["Alpha"], bsdf.inputs["Alpha"])


@classes.register
class ShaderNodePso2Ngs(ShaderNodePso2NgsBase):
    bl_name = "ShaderNodePso2Ngs"
    bl_label = "PSO2 NGS"
    bl_icon = "NONE"


@classes.register
class ShaderNodePso2NgsSkin(ShaderNodePso2NgsBase):
    bl_name = "ShaderNodePso2NgsSkin"
    bl_label = "PSO2 NGS Skin"
    bl_icon = "NONE"

    def _build(self, node_tree):
        super()._build(node_tree)

        bsdf = cast(
            bpy.types.ShaderNodeBsdfPrincipled, node_tree.nodes["Principled BSDF"]
        )

        bsdf.subsurface_method = "RANDOM_WALK_SKIN"
        bsdf.inputs["Subsurface Weight"].default_value = 0.2  # type: ignore
