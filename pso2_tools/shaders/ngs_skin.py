from typing import Optional
import bpy

from pso2_tools.colors import Colors
from pso2_tools.shaders import shader, ngs_common


class NgsSkinMaterial(shader.ShaderBuilder):
    skin_textures: shader.MaterialTextures
    inner_textures: Optional[shader.MaterialTextures]

    def __init__(
        self,
        material: bpy.types.Material,
        skin_textures: shader.MaterialTextures,
        inner_textures: Optional[shader.MaterialTextures] = None,
    ):
        super().__init__(material)
        self.skin_textures = skin_textures
        self.inner_textures = inner_textures

    def build(self, context: bpy.types.Context):
        x2 = 18

        build = self.init_tree()
        output = build.add_node("ShaderNodeOutputMaterial", (x2 + 24, 11))

        # ========== Skin ==========

        skin_frame = build.add_node("NodeFrame", (0, 12))
        skin_frame.label = "Skin"

        skin_group: ngs_common.ShaderNodePso2NgsSkin = build.add_node(
            "ShaderNodePso2NgsSkin", (12, 9)
        )
        skin_group.parent = skin_frame

        # Base Color
        diffuse = build.add_node("ShaderNodeTexImage", (0, 12))
        diffuse.label = "Skin Diffuse"
        diffuse.image = self.skin_textures.diffuse
        diffuse.parent = skin_frame

        build.add_link(diffuse.outputs["Color"], skin_group.inputs["Diffuse"])
        build.add_link(diffuse.outputs["Alpha"], skin_group.inputs["Alpha"])

        # Skin Tone
        multi = build.add_node("ShaderNodeTexImage", (0, 6))
        multi.label = "Skin Multi Color"
        multi.image = self.skin_textures.multi
        multi.parent = skin_frame

        build.add_link(multi.outputs["Color"], skin_group.inputs["Mask RGB"])

        colors = build.add_node("ShaderNodeGroup", (6, 8))
        colors.label = "Colors"
        colors.parent = skin_frame
        colors.node_tree = shader.get_color_channels_node(context)

        build.add_color_link(Colors.MainSkin, colors, skin_group.inputs["Color 1"])
        build.add_color_link(Colors.SubSkin, colors, skin_group.inputs["Color 2"])

        # Specular Map
        specular = build.add_node("ShaderNodeTexImage", (0, 0))
        specular.label = "Skin Specular"
        specular.image = self.skin_textures.specular
        specular.parent = skin_frame

        build.add_link(specular.outputs["Color"], skin_group.inputs["Specular RGB"])
        build.add_link(specular.outputs["Alpha"], skin_group.inputs["Specular A"])

        # Normal Map
        normal = build.add_node("ShaderNodeTexImage", (0, -6))
        normal.label = "Skin Normal"
        normal.image = self.skin_textures.normal
        normal.parent = skin_frame

        build.add_link(normal.outputs["Color"], skin_group.inputs["Normal"])

        # Unknown
        texture_o = build.add_node("ShaderNodeTexImage", (0, -12))
        texture_o.label = "Skin Texture O"
        texture_o.image = self.skin_textures.texture_o
        texture_o.parent = skin_frame

        build.add_link(texture_o.outputs["Color"], skin_group.inputs["Texture O"])

        # ========== Innerwear ==========

        inner_frame = build.add_node("NodeFrame", (0, 12))
        inner_frame.label = "Innerwear"

        inner_group: ngs_common.ShaderNodePso2Ngs = build.add_node(
            "ShaderNodePso2Ngs", (x2 + 12, 9)
        )
        inner_group.parent = inner_frame

        # Base Color
        in_diffuse = build.add_node("ShaderNodeTexImage", (x2 + 0, 12))
        in_diffuse.label = "Innerwear Diffuse"
        in_diffuse.parent = inner_frame
        if self.inner_textures:
            in_diffuse.image = self.inner_textures.diffuse

        build.add_link(in_diffuse.outputs["Color"], inner_group.inputs["Diffuse"])
        build.add_link(in_diffuse.outputs["Alpha"], inner_group.inputs["Alpha"])

        # Skin Tone
        in_multi = build.add_node("ShaderNodeTexImage", (x2 + 0, 6))
        in_multi.label = "Innerwear Multi Color"
        in_multi.parent = inner_frame
        if self.inner_textures:
            in_multi.image = self.inner_textures.multi

        build.add_link(in_multi.outputs["Color"], inner_group.inputs["Mask RGB"])

        in_colors = build.add_node("ShaderNodeGroup", (x2 + 6, 8))
        in_colors.label = "Colors"
        in_colors.parent = inner_frame
        in_colors.node_tree = shader.get_color_channels_node(context)

        build.add_color_link(Colors.Inner1, in_colors, inner_group.inputs["Color 1"])
        build.add_color_link(Colors.Inner1, in_colors, inner_group.inputs["Color 2"])

        # Specular Map
        in_specular = build.add_node("ShaderNodeTexImage", (x2 + 0, 0))
        in_specular.label = "Innerwear Specular"
        in_specular.parent = inner_frame
        if self.inner_textures:
            in_specular.image = self.inner_textures.specular

        build.add_link(in_specular.outputs["Color"], inner_group.inputs["Specular RGB"])
        build.add_link(in_specular.outputs["Alpha"], inner_group.inputs["Specular A"])

        # Normal Map
        in_normal = build.add_node("ShaderNodeTexImage", (x2 + 0, -6))
        in_normal.label = "Innerwear Normal"
        in_normal.parent = inner_frame
        if self.inner_textures:
            in_normal.image = self.inner_textures.normal

        build.add_link(in_normal.outputs["Color"], inner_group.inputs["Normal"])

        # ========== Mix ==========

        mask = build.add_node("ShaderNodeTexImage", (x2 + 0, -12))
        mask.label = "Innerwear Mask"
        mask.parent = inner_frame
        if self.inner_textures:
            mask.image = self.inner_textures.layer

        mask_rgb = build.add_node("ShaderNodeSeparateColor", (x2 + 6, -12))
        mask_rgb.mode = "RGB"
        mask_rgb.parent = inner_frame
        build.add_link(mask.outputs["Color"], mask_rgb.inputs["Color"])
        # TODO: how do R, G, B channels work?
        # Upper body is colored blue? Lower body is colored green?

        inner_enable = build.add_node("ShaderNodeValue", (x2 + 6, -8))
        inner_enable.label = "Show Innerwear"
        inner_enable.outputs[0].default_value = 1

        mix_fac = build.add_node("ShaderNodeMath", (x2 + 12, -6))
        mix_fac.operation = "MULTIPLY"
        mix_fac.use_clamp = True

        build.add_link(inner_enable.outputs[0], mix_fac.inputs[0])
        build.add_link(mask_rgb.outputs["R"], mix_fac.inputs[1])

        mix = build.add_node("ShaderNodeMixShader", (x2 + 18, 11))
        build.add_link(mix_fac.outputs[0], mix.inputs["Fac"])
        build.add_link(skin_group.outputs["BSDF"], mix.inputs[1])
        build.add_link(inner_group.outputs["BSDF"], mix.inputs[2])

        build.add_link(mix.outputs[0], output.inputs["Surface"])
