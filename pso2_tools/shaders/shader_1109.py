import bpy

from ..colors import ColorId, ColorMapping
from ..material import MaterialTextures
from . import builder, color_channels, types
from .colorize import ShaderNodePso2Colorize
from .ngs import ShaderNodePso2NgsSkin


class Shader1109(builder.ShaderBuilder):
    """NGS ear shader"""

    def __init__(
        self,
        mat: bpy.types.Material,
        data: types.ShaderData,
    ):
        super().__init__(mat)
        self.data = data

    @property
    def textures(self) -> MaterialTextures:
        return self.data.textures

    @property
    def colors(self) -> ColorMapping:
        return self.data.color_map

    def build(self, context):
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (24, 6))

        # TODO: is skin shader accurate here? There are some pieces like
        # machine kitten ears that use 1109 for parts that aren't skin.
        shader_group: ShaderNodePso2NgsSkin = tree.add_node(
            "ShaderNodePso2NgsSkin", (18, 6)
        )
        tree.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 18))
        diffuse.label = "Diffuse"
        diffuse.image = self.textures.default.diffuse

        tree.add_link(diffuse.outputs["Alpha"], shader_group.inputs["Alpha"])

        # Color Mask
        mask = tree.add_node("ShaderNodeTexImage", (0, 12))
        mask.label = "Color Mask"
        mask.image = self.textures.default.mask

        colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (12, 14)
        )

        tree.add_link(diffuse.outputs["Color"], colorize.inputs["Input"])
        tree.add_link(colorize.outputs["Result"], shader_group.inputs["Diffuse"])

        tree.add_link(mask.outputs["Color"], colorize.inputs["Mask RGB"])
        if self.colors.alpha != ColorId.UNUSED:
            tree.add_link(mask.outputs["Alpha"], colorize.inputs["Mask A"])

        channels = tree.add_node("ShaderNodeGroup", (7, 10))
        channels.label = "Colors"
        channels.node_tree = color_channels.get_color_channels_node(context)

        tree.add_color_link(self.colors.red, channels, colorize.inputs["Color 1"])
        tree.add_color_link(self.colors.green, channels, colorize.inputs["Color 2"])
        tree.add_color_link(self.colors.blue, channels, colorize.inputs["Color 3"])
        tree.add_color_link(self.colors.alpha, channels, colorize.inputs["Color 4"])

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (0, 6))
        multi.label = "Multi Map"
        multi.image = self.textures.default.multi

        tree.add_link(multi.outputs["Color"], shader_group.inputs["Multi RGB"])
        tree.add_link(multi.outputs["Alpha"], shader_group.inputs["Multi A"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (0, 0))
        normal.label = "Normal Map"
        normal.image = self.textures.default.normal

        tree.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])
