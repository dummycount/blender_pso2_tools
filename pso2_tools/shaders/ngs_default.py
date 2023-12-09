import bpy

from pso2_tools.colors import Colors
from pso2_tools.object_info import ObjectInfo
from pso2_tools.shaders import shader, ngs_common
from pso2_tools.shaders.shader import MaterialTextures


class NgsDefaultMaterial(shader.ShaderBuilder):
    textures: MaterialTextures
    colors: list[Colors]
    object_info: ObjectInfo

    def __init__(
        self,
        material: bpy.types.Material,
        textures: MaterialTextures,
        colors: list[Colors],
        object_info: ObjectInfo,
    ):
        super().__init__(material)
        self.textures = textures
        self.colors = colors
        self.object_info = object_info

    def build(self, context: bpy.types.Context):
        build = self.init_tree()

        shader_group: ngs_common.ShaderNodePso2Ngs = build.add_node(
            "ShaderNodePso2Ngs", (12, 9)
        )

        output = build.add_node("ShaderNodeOutputMaterial", (18, 9))
        build.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Base Color
        diffuse = build.add_node("ShaderNodeTexImage", (0, 12))
        diffuse.label = "Diffuse"
        diffuse.image = self.textures.diffuse

        build.add_link(diffuse.outputs["Color"], shader_group.inputs["Diffuse"])
        build.add_link(diffuse.outputs["Alpha"], shader_group.inputs["Alpha"])

        # Custom Colors
        multi = build.add_node("ShaderNodeTexImage", (0, 6))
        multi.label = "Multi Color"
        multi.image = self.textures.layer if self.is_cast_part else self.textures.multi

        build.add_link(multi.outputs["Color"], shader_group.inputs["Mask RGB"])
        if self._channel(3) != Colors.Unused:
            build.add_link(multi.outputs["Alpha"], shader_group.inputs["Mask A"])

        colors = build.add_node("ShaderNodeGroup", (6, 12))
        colors.label = "Colors"
        colors.node_tree = shader.get_color_channels_node(context)

        build.add_color_link(self._channel(0), colors, shader_group.inputs["Color 1"])
        build.add_color_link(self._channel(1), colors, shader_group.inputs["Color 2"])
        build.add_color_link(self._channel(2), colors, shader_group.inputs["Color 3"])
        build.add_color_link(self._channel(3), colors, shader_group.inputs["Color 4"])

        # Specular Map
        specular = build.add_node("ShaderNodeTexImage", (0, 0))
        specular.label = "Specular"
        specular.image = self.textures.specular

        build.add_link(specular.outputs["Color"], shader_group.inputs["Specular RGB"])
        build.add_link(specular.outputs["Alpha"], shader_group.inputs["Specular A"])

        # Normal Map
        normal = build.add_node("ShaderNodeTexImage", (0, -6))
        normal.label = "Normal"
        normal.image = self.textures.normal

        build.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])

        # Unknown
        texture_o = build.add_node("ShaderNodeTexImage", (0, -12))
        texture_o.label = "Texture O"
        texture_o.image = self.textures.texture_o

        build.add_link(texture_o.outputs["Color"], shader_group.inputs["Texture O"])

        if self.is_cast_part:
            uv = build.add_node("ShaderNodeUVMap", (-12, 0))
            uv.uv_map = "UVChannel_1"

            rescale = self.object_info.uv_mapping

            map_range = build.add_node("ShaderNodeMapRange", (-6, 0))
            map_range.data_type = "FLOAT_VECTOR"
            map_range.inputs[7].default_value[0] = rescale.from_u_min
            map_range.inputs[8].default_value[0] = rescale.from_u_max
            map_range.inputs[9].default_value[0] = rescale.to_u_min
            map_range.inputs[10].default_value[0] = rescale.to_u_max

            build.add_link(uv.outputs["UV"], map_range.inputs[6])

            build.add_link(map_range.outputs[1], diffuse.inputs["Vector"])
            build.add_link(map_range.outputs[1], multi.inputs["Vector"])
            build.add_link(map_range.outputs[1], specular.inputs["Vector"])
            build.add_link(map_range.outputs[1], normal.inputs["Vector"])
            build.add_link(map_range.outputs[1], texture_o.inputs["Vector"])

    @property
    def is_cast_part(self):
        return self.object_info.is_cast_part

    def _channel(self, idx: int):
        try:
            return self.colors[idx]
        except IndexError:
            return Colors.Unused
