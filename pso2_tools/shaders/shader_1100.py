import bpy

from ..colors import ColorId, ColorMapping
from ..material import MaterialTextures, UVMapping
from . import builder, color_channels, types
from .colorize import ShaderNodePso2Colorize
from .ngs import ShaderNodePso2Ngs


class Shader1100(builder.ShaderBuilder):
    """Default NGS shader"""

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

    @property
    def uv_map(self) -> UVMapping:
        return self.data.uv_map

    def build(self, context):
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (20, 10))

        shader_group: ShaderNodePso2Ngs = tree.add_node("ShaderNodePso2Ngs", (16, 10))
        tree.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 18), name="Diffuse")
        diffuse.image = self.textures.default.diffuse

        tree.add_link(diffuse.outputs["Alpha"], shader_group.inputs["Alpha"])

        # Color Mask
        mask = tree.add_node("ShaderNodeTexImage", (0, 12), name="Color Mask")
        mask.image = self.textures.default.mask

        colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (12, 15)
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

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (0, 6), name="Multi Map")
        multi.image = self.textures.default.multi

        tree.add_link(multi.outputs["Color"], shader_group.inputs["Multi RGB"])
        tree.add_link(multi.outputs["Alpha"], shader_group.inputs["Multi A"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (0, 0), name="Normal Map")
        normal.image = self.textures.default.normal

        tree.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])

        # Cast part UV adjustment
        if self.uv_map:
            uv = tree.add_node("ShaderNodeUVMap", (-12, 6))
            uv.uv_map = "UVChannel_1"

            map_range = tree.add_node(
                "ShaderNodeMapRange", (-6, 6), name="Cast UV Rescale"
            )
            map_range.data_type = "FLOAT_VECTOR"
            map_range.clamp = False
            map_range.inputs[7].default_value[0] = self.data.uv_map.from_u_min
            map_range.inputs[8].default_value[0] = self.data.uv_map.from_u_max
            map_range.inputs[9].default_value[0] = self.data.uv_map.to_u_min
            map_range.inputs[10].default_value[0] = self.data.uv_map.to_u_max

            tree.add_link(uv.outputs["UV"], map_range.inputs[6])

            tree.add_link(map_range.outputs[1], diffuse.inputs["Vector"])
            tree.add_link(map_range.outputs[1], mask.inputs["Vector"])
            tree.add_link(map_range.outputs[1], multi.inputs["Vector"])
            tree.add_link(map_range.outputs[1], normal.inputs["Vector"])
