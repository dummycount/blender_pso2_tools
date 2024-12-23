import bpy

from .. import classes
from ..colors import ColorId, ColorMapping
from . import builder, group
from .colorize import ShaderNodePso2Colorize
from .colors import ShaderNodePso2Colorchannels


class Shader1103(builder.ShaderBuilder):
    """NGS hair shader"""

    @property
    def textures(self):
        return self.data.textures

    @property
    def colors(self) -> ColorMapping:
        return self.data.color_map or ColorMapping()

    def build(self, context):
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (24, 6))

        shader_group: ShaderNodePso2NgsHair = tree.add_node(
            "ShaderNodePso2NgsHair", (18, 6)
        )  # type: ignore
        tree.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Non-alpha Texture UVs
        uv = tree.add_node("ShaderNodeUVMap", (-8, 0), name="UVs")
        uv.uv_map = "UVChannel_2"

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 18), name="Diffuse")
        diffuse.image = self.textures.default.diffuse

        tree.add_link(uv.outputs[0], diffuse.inputs["Vector"])

        # Color Mask
        mask = tree.add_node("ShaderNodeTexImage", (0, 12), name="Color Mask")
        mask.image = self.textures.default.mask

        tree.add_link(uv.outputs[0], mask.inputs["Vector"])

        colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (12, 14)
        )  # type: ignore

        tree.add_link(diffuse.outputs["Color"], colorize.inputs["Input"])
        tree.add_link(colorize.outputs["Result"], shader_group.inputs["Diffuse"])

        tree.add_link(mask.outputs["Color"], colorize.inputs["Mask RGB"])
        if self.colors.alpha != ColorId.UNUSED:
            tree.add_link(mask.outputs["Alpha"], colorize.inputs["Mask A"])

        channels: ShaderNodePso2Colorchannels = tree.add_node(
            "ShaderNodePso2Colorchannels", (7, 10), name="Colors"
        )  # type: ignore

        tree.add_color_link(self.colors.red, channels, colorize.inputs["Color 1"])
        tree.add_color_link(self.colors.green, channels, colorize.inputs["Color 2"])
        tree.add_color_link(self.colors.blue, channels, colorize.inputs["Color 3"])
        tree.add_color_link(self.colors.alpha, channels, colorize.inputs["Color 4"])
        colorize.set_colors_used(self.colors)

        # Alpha
        alpha = tree.add_node("ShaderNodeTexImage", (0, 6), name="Alpha")
        alpha.image = self.textures.default.alpha

        tree.add_link(alpha.outputs["Color"], shader_group.inputs["Alpha"])

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (0, 0), name="Multi Map")
        multi.image = self.textures.default.multi

        tree.add_link(uv.outputs[0], multi.inputs["Vector"])
        tree.add_link(multi.outputs["Color"], shader_group.inputs["Multi RGB"])
        tree.add_link(multi.outputs["Alpha"], shader_group.inputs["Multi A"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (0, -6), name="Normal Map")
        normal.image = self.textures.default.normal

        tree.add_link(uv.outputs[0], normal.inputs["Vector"])
        tree.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])


@classes.register
class ShaderNodePso2NgsHair(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2NgsHair"
    bl_label = "PSO2 NGS Hair"
    bl_icon = "NONE"

    def init(self, context):
        super().init(context)

        self.input(bpy.types.NodeSocketColor, "Diffuse").default_value = (1, 0, 1, 1)
        self.input(bpy.types.NodeSocketFloat, "Alpha").default_value = 1

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

        multi_rgb = tree.add_node("ShaderNodeSeparateColor")
        multi_rgb.name = "Multi Map RGB"
        multi_rgb.label = multi_rgb.name
        multi_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Multi RGB"], multi_rgb.inputs["Color"])

        # TODO: how is the multi map used for hair?
        # R = 1
        # G = 1 or 0.5 on different hair strands
        # B = random chunks?
        # A = 0

        # ========== Base color ==========

        tree.add_link(group_inputs.outputs["Diffuse"], bsdf.inputs["Base Color"])
        tree.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])
