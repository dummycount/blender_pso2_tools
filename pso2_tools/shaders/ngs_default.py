from bpy.types import Material

from . import shader, ngs_common


class NgsDefaultMaterial(shader.ShaderBuilder):
    textures: shader.MaterialTextures
    colors: shader.ColorGroup

    def __init__(
        self,
        material: Material,
        textures: shader.MaterialTextures,
        colors: shader.ColorGroup,
    ):
        super().__init__(material)
        self.textures = textures
        self.colors = colors

    def build(self):
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
        multi.image = self.textures.multi

        build.add_link(multi.outputs["Color"], shader_group.inputs["Mask RGB"])
        # TODO: connect Mask A if it appears to be used

        colors = build.add_node("ShaderNodeGroup", (6, 8))
        colors.label = "Outfit Colors"
        colors.node_tree = shader.get_custom_color_group(self.colors)

        build.add_link(colors.outputs[0], shader_group.inputs["Color 1"])
        build.add_link(colors.outputs[1], shader_group.inputs["Color 2"])

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
