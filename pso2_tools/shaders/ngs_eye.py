from bpy.types import Material

from pso2_tools.shaders import default_colors, shader, ngs_common


class NgsEyeMaterial(shader.ShaderBuilder):
    textures: shader.MaterialTextures
    colors: shader.ColorGroup

    def __init__(
        self,
        material: Material,
        textures: shader.MaterialTextures,
        colors: shader.ColorGroup,
        eye_index=0,
    ):
        super().__init__(material)
        self.textures = textures
        self.colors = colors
        self.eye_index = eye_index

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

        colors = build.add_node("ShaderNodeGroup", (6, 8))
        colors.label = "Eye Colors"
        colors.node_tree = shader.get_custom_color_group(self.colors)

        build.add_link(colors.outputs[self.eye_index], shader_group.inputs["Color 1"])

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
        # TODO: overlays the main image? Need a special shader group to handle this.
        # Tear layer has no UVs so this probably doesn't belong to it.
        texture_v = build.add_node("ShaderNodeTexImage", (0, -12))
        texture_v.label = "Texture V"
        texture_v.image = self.textures.texture_v

        # build.add_link(texture_v.outputs["Color"], shader_group.inputs["Texture V"])


class NgsEyeTearMaterial(shader.ShaderBuilder):
    def build(self):
        build = self.init_tree()
        output = build.add_node("ShaderNodeOutputMaterial", (6, 0))

        # TODO: Not sure how this should look. Just make it totally transparent for now.
        bsdf = build.add_node("ShaderNodeBsdfTransparent", (0, 0))
        bsdf.inputs["Color"].default_value = default_colors.WHITE

        build.add_link(bsdf.outputs["BSDF"], output.inputs["Surface"])
