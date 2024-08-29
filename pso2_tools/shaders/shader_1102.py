import bpy

from ..colors import ColorId
from . import builder, color_channels, types
from .colorize import ShaderNodePso2Colorize
from .mix import ShaderNodePso2MixTexture
from .ngs import ShaderNodePso2Ngs, ShaderNodePso2NgsSkin


class Shader1102(builder.ShaderBuilder):
    """NGS skin shader"""

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

        output = tree.add_node("ShaderNodeOutputMaterial", (50, 0))

        # ========== Skin ==========

        skin = tree.add_group("Skin", (0, 0))

        skin_group: ShaderNodePso2NgsSkin = skin.add_node(
            "ShaderNodePso2NgsSkin", (30, 6)
        )

        # Diffuse
        diffuse_0 = skin.add_node("ShaderNodeTexImage", (0, 18), name="Diffuse")
        diffuse_0.image = self.textures.skin_0.diffuse or self.textures.default.diffuse

        diffuse_1 = skin.add_node("ShaderNodeTexImage", (6, 18), name="Diffse Muscle")
        diffuse_1.image = self.textures.skin_1.diffuse or self.textures.default.diffuse

        muscularity = skin.add_node("ShaderNodeAttribute", (12, 9), name="Muscularity")
        muscularity.attribute_type = "VIEW_LAYER"
        muscularity.attribute_name = "Muscularity"

        diffuse_mix: ShaderNodePso2MixTexture = skin.add_node(
            "ShaderNodePso2MixTexture", (18, 18), name="Diffuse Mix"
        )

        tree.add_link(muscularity.outputs["Fac"], diffuse_mix.inputs["Factor"])
        tree.add_link(diffuse_0.outputs["Color"], diffuse_mix.inputs["Color 1"])
        tree.add_link(diffuse_0.outputs["Alpha"], diffuse_mix.inputs["Alpha 1"])
        tree.add_link(diffuse_1.outputs["Color"], diffuse_mix.inputs["Color 2"])
        tree.add_link(diffuse_1.outputs["Alpha"], diffuse_mix.inputs["Alpha 2"])

        tree.add_link(diffuse_mix.outputs["Alpha"], skin_group.inputs["Alpha"])

        # Color Mask
        mask_0 = skin.add_node("ShaderNodeTexImage", (0, 12), name="Color Mask")
        mask_0.image = self.textures.skin_0.mask or self.textures.default.mask

        mask_1 = skin.add_node("ShaderNodeTexImage", (6, 12), name="Color Mask Muscle")
        mask_1.image = self.textures.skin_1.mask or self.textures.default.mask

        mask_mix: ShaderNodePso2MixTexture = skin.add_node(
            "ShaderNodePso2MixTexture", (18, 12), name="Color Mask Mix"
        )

        tree.add_link(muscularity.outputs["Fac"], mask_mix.inputs["Factor"])
        tree.add_link(mask_0.outputs["Color"], mask_mix.inputs["Color 1"])
        tree.add_link(mask_0.outputs["Alpha"], mask_mix.inputs["Alpha 1"])
        tree.add_link(mask_1.outputs["Color"], mask_mix.inputs["Color 2"])
        tree.add_link(mask_1.outputs["Alpha"], mask_mix.inputs["Alpha 2"])

        colorize: ShaderNodePso2Colorize = skin.add_node(
            "ShaderNodePso2Colorize", (26, 14), name="Skin Colorize"
        )

        tree.add_link(diffuse_mix.outputs["Color"], colorize.inputs["Input"])
        tree.add_link(mask_mix.outputs["Color"], colorize.inputs["Mask RGB"])
        tree.add_link(colorize.outputs["Result"], skin_group.inputs["Diffuse"])

        channels = skin.add_node("ShaderNodeGroup", (22, 10), name="Colors")
        channels.node_tree = color_channels.get_color_channels_node(context)

        tree.add_color_link(ColorId.MAIN_SKIN, channels, colorize.inputs["Color 1"])
        tree.add_color_link(ColorId.SUB_SKIN, channels, colorize.inputs["Color 2"])

        # Multi Map
        multi_0 = skin.add_node("ShaderNodeTexImage", (0, 6), name="Multi Map")
        multi_0.image = self.textures.skin_0.multi or self.textures.default.multi

        multi_1 = skin.add_node("ShaderNodeTexImage", (6, 6), name="Multi Map Muscle")
        multi_1.image = self.textures.skin_1.multi or self.textures.default.multi

        multi_mix: ShaderNodePso2MixTexture = skin.add_node(
            "ShaderNodePso2MixTexture", (18, 6), name="Multi Map Mix"
        )

        tree.add_link(muscularity.outputs["Fac"], multi_mix.inputs["Factor"])
        tree.add_link(multi_0.outputs["Color"], multi_mix.inputs["Color 1"])
        tree.add_link(multi_0.outputs["Alpha"], multi_mix.inputs["Alpha 1"])
        tree.add_link(multi_1.outputs["Color"], multi_mix.inputs["Color 2"])
        tree.add_link(multi_1.outputs["Alpha"], multi_mix.inputs["Alpha 2"])

        tree.add_link(multi_mix.outputs["Color"], skin_group.inputs["Multi RGB"])
        tree.add_link(multi_mix.outputs["Alpha"], skin_group.inputs["Multi A"])

        # Normal Map
        normal_0 = skin.add_node("ShaderNodeTexImage", (0, 0), name="Normal Map")
        normal_0.image = self.textures.skin_0.normal or self.textures.default.normal

        normal_1 = skin.add_node("ShaderNodeTexImage", (6, 0), name="Normal Map Muscle")
        normal_1.image = self.textures.skin_1.normal or self.textures.default.normal

        normal_mix: ShaderNodePso2MixTexture = skin.add_node(
            "ShaderNodePso2MixTexture", (18, 0), name="Normal Map Mix"
        )

        tree.add_link(muscularity.outputs["Fac"], normal_mix.inputs["Factor"])
        tree.add_link(normal_0.outputs["Color"], normal_mix.inputs["Color 1"])
        tree.add_link(normal_1.outputs["Color"], normal_mix.inputs["Color 2"])

        tree.add_link(normal_mix.outputs["Color"], skin_group.inputs["Normal"])

        # ========== Innerwear ==========

        inner = tree.add_group("Innerwear", (12, -26))

        in_group: ShaderNodePso2Ngs = inner.add_node("ShaderNodePso2Ngs", (18, 6))

        # Diffuse
        in_diffuse = inner.add_node(
            "ShaderNodeTexImage", (0, 18), name="Innerwear Diffuse"
        )
        in_diffuse.image = self.textures.inner.diffuse

        tree.add_link(in_diffuse.outputs["Alpha"], in_group.inputs["Alpha"])

        # Color Mask
        in_mask = inner.add_node(
            "ShaderNodeTexImage", (0, 12), name="Innerwear Color Mask"
        )
        in_mask.image = self.textures.inner.mask

        in_colorize: ShaderNodePso2Colorize = inner.add_node(
            "ShaderNodePso2Colorize", (12, 14), name="Innerwear Colorize"
        )

        tree.add_link(in_diffuse.outputs["Color"], in_colorize.inputs["Input"])
        tree.add_link(in_mask.outputs["Color"], in_colorize.inputs["Mask RGB"])
        tree.add_link(in_colorize.outputs["Result"], in_group.inputs["Diffuse"])

        channels = inner.add_node("ShaderNodeGroup", (8, 10), name="Colors")
        channels.node_tree = color_channels.get_color_channels_node(context)

        tree.add_color_link(ColorId.INNER1, channels, in_colorize.inputs["Color 1"])
        tree.add_color_link(ColorId.INNER2, channels, in_colorize.inputs["Color 2"])

        # Multi Map
        in_multi = inner.add_node(
            "ShaderNodeTexImage", (0, 6), name="Innerwear Multi Map"
        )
        in_multi.image = self.textures.inner.multi

        tree.add_link(in_multi.outputs["Color"], in_group.inputs["Multi RGB"])
        tree.add_link(in_multi.outputs["Alpha"], in_group.inputs["Multi A"])

        # Normal Map
        in_normal = inner.add_node(
            "ShaderNodeTexImage", (0, 0), name="Innerwear Normal Map"
        )
        in_normal.image = self.textures.inner.normal

        tree.add_link(in_normal.outputs["Color"], in_group.inputs["Normal"])

        # TODO: add a bodypaint layer?

        # ========== Mix ==========

        layer = tree.add_node("ShaderNodeTexImage", (36, 12), name="Layer")
        layer.image = self.textures.inner.layer

        layer_rgb = tree.add_node("ShaderNodeSeparateColor", (42, 12))
        layer_rgb.mode = "RGB"

        tree.add_link(layer.outputs["Color"], layer_rgb.inputs["Color"])

        in_hide = tree.add_node("ShaderNodeAttribute", (38, 16), name="Hide Innerwear")
        in_hide.attribute_type = "VIEW_LAYER"
        in_hide.attribute_name = "Hide Innerwear"

        in_show = tree.add_node("ShaderNodeMath", (42, 16), name="Show Innerwear")
        in_show.operation = "SUBTRACT"
        in_show.inputs[0].default_value = 1

        tree.add_link(in_hide.outputs["Fac"], in_show.inputs[1])

        mix_fac = tree.add_node("ShaderNodeMath", (46, 12))
        mix_fac.operation = "MULTIPLY"
        mix_fac.use_clamp = True

        tree.add_link(in_show.outputs[0], mix_fac.inputs[0])
        tree.add_link(layer_rgb.outputs["Red"], mix_fac.inputs[1])

        mix = tree.add_node("ShaderNodeMixShader", (46, 0))
        tree.add_link(mix_fac.outputs[0], mix.inputs["Fac"])
        tree.add_link(skin_group.outputs["BSDF"], mix.inputs[1])
        tree.add_link(in_group.outputs["BSDF"], mix.inputs[2])

        tree.add_link(mix.outputs[0], output.inputs["Surface"])
