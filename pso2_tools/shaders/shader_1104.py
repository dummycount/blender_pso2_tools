import bpy

from .. import classes
from ..colors import ColorId, ColorMapping
from . import builder, group
from .colorize import ShaderNodePso2Colorize
from .colors import ShaderNodePso2Colorchannels


class Shader1104(builder.ShaderBuilder):
    """NGS eye shader"""

    @property
    def textures(self):
        return self.data.textures

    @property
    def colors(self) -> ColorMapping:
        return self.data.color_map or ColorMapping()

    def build(self, context):
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (24, 6))

        shader_group: ShaderNodePso2NgsEye = tree.add_node(
            "ShaderNodePso2NgsEye", (18, 6)
        )  # type: ignore
        tree.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 18), name="Diffuse")
        diffuse.image = self.textures.default.diffuse

        # Alpha seems to be used for something different than alpha
        # tree.add_link(diffuse.outputs["Alpha"], shader_group.inputs["Alpha"])

        # Color Mask
        mask = tree.add_node("ShaderNodeTexImage", (0, 12), name="Color Mask")
        mask.image = self.textures.default.mask

        colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (12, 14)
        )  # type: ignore

        tree.add_link(diffuse.outputs["Color"], colorize.inputs["Input"])
        tree.add_link(colorize.outputs["Result"], shader_group.inputs["Diffuse"])

        tree.add_link(mask.outputs["Color"], colorize.inputs["Mask RGB"])
        tree.add_link(mask.outputs["Alpha"], colorize.inputs["Mask A"])

        channels: ShaderNodePso2Colorchannels = tree.add_node(
            "ShaderNodePso2Colorchannels", (7, 10), name="Colors"
        )  # type: ignore

        color = ColorId.LEFT_EYE if "eye_l" in self.material.name else ColorId.RIGHT_EYE
        tree.add_color_link(color, channels, colorize.inputs["Color 1"])
        colorize.set_colors_used([1])

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (0, 6), name="Multi Map")
        multi.image = self.textures.default.multi

        tree.add_link(multi.outputs["Color"], shader_group.inputs["Multi RGB"])
        tree.add_link(multi.outputs["Alpha"], shader_group.inputs["Multi A"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (0, 0), name="Normal Map")
        normal.image = self.textures.default.normal

        tree.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])


@classes.register
class ShaderNodePso2NgsEye(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Eye"
    bl_label = "PSO2 Eye"
    bl_icon = "NONE"

    def init(self, context):
        super().init(context)

        self.input(bpy.types.NodeSocketColor, "Diffuse").default_value = (1, 0, 1, 1)
        self.input(bpy.types.NodeSocketFloat, "Alpha").default_value = 1
        self.input(bpy.types.NodeSocketColor, "Multi RGB").default_value = (0, 1, 1, 1)

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketColor", "Diffuse")
        tree.new_input("NodeSocketFloat", "Alpha")
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

        # TODO: does this mean the same things as in the default shader?

        multi_rgb = tree.add_node("ShaderNodeSeparateColor", name="Multi Map RGB")
        multi_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Multi RGB"], multi_rgb.inputs["Color"])
        tree.add_link(multi_rgb.outputs["Red"], bsdf.inputs["Metallic"])

        tree.add_link(multi_rgb.outputs["Green"], bsdf.inputs["Roughness"])

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
        tree.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])
