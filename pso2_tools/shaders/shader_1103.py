import bpy

from .. import classes
from ..colors import ColorId
from . import builder, color_channels, types
from .colorize import ShaderNodePso2Colorize


class Shader1103(builder.ShaderBuilder):
    """NGS hair shader"""

    def __init__(
        self,
        mat: bpy.types.Material,
        data: types.ShaderData,
    ):
        super().__init__(mat)
        self.data = data

    @property
    def textures(self):
        return self.data.textures

    @property
    def colors(self):
        return self.data.color_map

    def build(self, context):
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (24, 6))

        shader_group: ShaderNodePso2NgsHair = tree.add_node(
            "ShaderNodePso2NgsHair", (18, 6)
        )
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
        )

        tree.add_link(diffuse.outputs["Color"], colorize.inputs["Input"])
        tree.add_link(colorize.outputs["Result"], shader_group.inputs["Diffuse"])

        tree.add_link(mask.outputs["Color"], colorize.inputs["Mask RGB"])
        if self.colors.alpha != ColorId.UNUSED:
            tree.add_link(mask.outputs["Alpha"], colorize.inputs["Mask A"])

        channels = tree.add_node("ShaderNodeGroup", (7, 10), name="Colors")
        channels.node_tree = color_channels.get_color_channels_node(context)

        tree.add_color_link(self.colors.red, channels, colorize.inputs["Color 1"])
        tree.add_color_link(self.colors.green, channels, colorize.inputs["Color 2"])
        tree.add_color_link(self.colors.blue, channels, colorize.inputs["Color 3"])
        tree.add_color_link(self.colors.alpha, channels, colorize.inputs["Color 4"])

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
class ShaderNodePso2NgsHair(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2NgsHair"
    bl_label = "PSO2 NGS Hair"
    bl_icon = "NONE"

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.name, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

        self.inputs["Diffuse"].default_value = (1, 0, 1, 1)
        self.inputs["Alpha"].default_value = 1

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self):
        tree = builder.NodeTreeBuilder(
            bpy.data.node_groups.new(self.name, "ShaderNodeTree")
        )

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

        return tree.tree
