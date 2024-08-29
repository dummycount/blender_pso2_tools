import bpy

from .. import classes
from ..colors import ColorId, ColorMapping
from ..material import MaterialTextures, UVMapping
from . import builder, color_channels, types
from .attributes import ShaderNodePso2ShowInnerwear
from .colorize import ShaderNodePso2Colorize
from .mix import ShaderNodePso2MixTexture


class Shader0100(builder.ShaderBuilder):
    """Default classic shader"""

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
        # Just guessing how this all fits together, but this seems to work...
        # This can probably be done much more simply.
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (40, 20))

        base_group: ShaderNodePso2Classic = tree.add_node(
            "ShaderNodePso2Classic", (34, 20)
        )
        tree.add_link(base_group.outputs["BSDF"], output.inputs["Surface"])

        channels = tree.add_node("ShaderNodeGroup", (12, 28), name="Colors")
        channels.node_tree = color_channels.get_color_channels_node(context)

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 36), name="Diffuse")
        diffuse.image = self.textures.default.diffuse

        tree.add_link(diffuse.outputs["Alpha"], base_group.inputs["Alpha"])

        # Skin Diffuse
        in_diffuse = tree.add_node(
            "ShaderNodeTexImage", (0, 24), name="Innerwear Diffuse"
        )
        in_diffuse.image = self.textures.inner.diffuse

        skin_alpha: ShaderNodePso2ShowInnerwear = tree.add_node(
            "ShaderNodePso2ShowInnerwear", (6, 22), name="Innerwear Alpha"
        )
        tree.add_link(in_diffuse.outputs["Alpha"], skin_alpha.inputs["Value"])

        skin_color = tree.add_node("ShaderNodeMix", (18, 25), name="Skin Color")
        skin_color.data_type = "RGBA"
        skin_color.blend_type = "MIX"
        skin_color.clamp_factor = True

        tree.add_color_link(ColorId.MAIN_SKIN, channels, skin_color.inputs["A"])
        tree.add_link(in_diffuse.outputs["Color"], skin_color.inputs["B"])
        tree.add_link(skin_alpha.outputs["Value"], skin_color.inputs["Factor"])

        # Color Mask
        mask = tree.add_node("ShaderNodeTexImage", (0, 30), name="Color Mask")
        mask.image = self.textures.default.mask

        colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (24, 30), name="Base Colorize"
        )

        tree.add_link(diffuse.outputs["Color"], colorize.inputs["Input"])

        tree.add_link(mask.outputs["Color"], colorize.inputs["Mask RGB"])
        # TODO: mask is opaque for cast part. Where does channel 4 come from?
        # if self.colors.alpha != ColorId.UNUSED:
        #     tree.add_link(mask.outputs["Alpha"], colorize.inputs["Mask A"])

        tree.add_color_link(self.colors.red, channels, colorize.inputs["Color 1"])
        tree.add_color_link(self.colors.green, channels, colorize.inputs["Color 2"])
        tree.add_color_link(self.colors.blue, channels, colorize.inputs["Color 3"])
        tree.add_color_link(self.colors.alpha, channels, colorize.inputs["Color 4"])

        in_mask = tree.add_node(
            "ShaderNodeTexImage", (0, 18), name="Innerwear Color Mask"
        )
        in_mask.image = self.textures.inner.mask

        mix_in_mask: ShaderNodePso2MixTexture = tree.add_node(
            "ShaderNodePso2MixTexture", (12, 20), name="Innerwear Mask Alpha"
        )

        tree.add_link(skin_alpha.outputs["Value"], mix_in_mask.inputs["Factor"])
        tree.add_link(in_mask.outputs["Color"], mix_in_mask.inputs["Color 2"])

        in_colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (24, 25), name="Innerwear Colorize"
        )

        tree.add_link(skin_color.outputs["Result"], in_colorize.inputs["Input"])
        tree.add_link(mix_in_mask.outputs["Color"], in_colorize.inputs["Mask RGB"])
        tree.add_color_link(ColorId.INNER1, channels, in_colorize.inputs["Color 3"])

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (6, 12), name="Multi Map")
        multi.image = self.textures.default.multi

        multi_rgb = tree.add_node(
            "ShaderNodeSeparateColor", (12, 16), name="Multi Map RGB"
        )
        multi_rgb.mode = "RGB"

        tree.add_link(multi.outputs["Color"], multi_rgb.inputs["Color"])

        skin_mix = tree.add_node("ShaderNodeMath", (18, 18), name="Skin Mix")
        skin_mix.operation = "MULTIPLY"
        skin_mix.use_clamp = True

        tree.add_link(skin_alpha.outputs["Value"], skin_mix.inputs[0])
        tree.add_link(multi_rgb.outputs["Green"], skin_mix.inputs[1])

        in_multi = tree.add_node(
            "ShaderNodeTexImage", (0, 12), name="Innerwear Multi Map"
        )
        in_multi.image = self.textures.inner.multi

        mix_multi: ShaderNodePso2MixTexture = tree.add_node(
            "ShaderNodePso2MixTexture", (24, 12), name="Multi Map Mix"
        )

        tree.add_link(skin_mix.outputs["Value"], mix_multi.inputs["Factor"])
        tree.add_link(multi.outputs["Color"], mix_multi.inputs["Color 1"])
        tree.add_link(multi.outputs["Alpha"], mix_multi.inputs["Alpha 1"])
        tree.add_link(in_multi.outputs["Color"], mix_multi.inputs["Color 2"])
        tree.add_link(in_multi.outputs["Alpha"], mix_multi.inputs["Alpha 2"])

        tree.add_link(mix_multi.outputs["Color"], base_group.inputs["Multi RGB"])
        tree.add_link(mix_multi.outputs["Alpha"], base_group.inputs["Multi A"])

        # Base/Skin Color Mix
        diffuse_mix = tree.add_node("ShaderNodeMix", (30, 25), name="Diffuse Mix")
        diffuse_mix.data_type = "RGBA"
        diffuse_mix.blend_type = "MIX"
        diffuse_mix.clamp_factor = True

        tree.add_link(multi_rgb.outputs["Green"], diffuse_mix.inputs["Factor"])
        tree.add_link(colorize.outputs["Result"], diffuse_mix.inputs["A"])
        tree.add_link(in_colorize.outputs["Result"], diffuse_mix.inputs["B"])

        tree.add_link(diffuse_mix.outputs["Result"], base_group.inputs["Diffuse"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (6, 6), name="Normal Map")
        normal.image = self.textures.default.normal

        in_normal = tree.add_node(
            "ShaderNodeTexImage", (0, 6), name="Innerwear Normal Map"
        )
        in_normal.image = self.textures.inner.normal

        mix_normal: ShaderNodePso2MixTexture = tree.add_node(
            "ShaderNodePso2MixTexture", (24, 8), name="Normal Map Mix"
        )

        tree.add_link(skin_mix.outputs["Value"], mix_normal.inputs["Factor"])
        tree.add_link(normal.outputs["Color"], mix_normal.inputs["Color 1"])
        tree.add_link(normal.outputs["Alpha"], mix_normal.inputs["Alpha 1"])
        tree.add_link(in_normal.outputs["Color"], mix_normal.inputs["Color 2"])
        tree.add_link(in_normal.outputs["Alpha"], mix_normal.inputs["Alpha 2"])

        tree.add_link(mix_normal.outputs["Color"], base_group.inputs["Normal"])

        # Cast part UV adjustment
        if self.uv_map:
            uv = tree.add_node("ShaderNodeUVMap", (-12, 24))
            uv.uv_map = "UVChannel_1"

            map_range = tree.add_node(
                "ShaderNodeMapRange", (-6, 24), name="Cast UV Rescale"
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

        # Innerwear UV
        in_uv = tree.add_node("ShaderNodeUVMap", (-12, 12))
        in_uv.uv_map = "UVChannel_1"

        map_range = tree.add_node(
            "ShaderNodeMapRange", (-6, 12), name="Innerwear UV Rescale"
        )
        map_range.data_type = "FLOAT_VECTOR"
        map_range.clamp = False
        map_range.inputs[7].default_value[0] = 0
        map_range.inputs[8].default_value[0] = 0.5
        map_range.inputs[9].default_value[0] = 0
        map_range.inputs[10].default_value[0] = 1

        tree.add_link(in_uv.outputs["UV"], map_range.inputs[6])

        tree.add_link(map_range.outputs[1], in_diffuse.inputs["Vector"])
        tree.add_link(map_range.outputs[1], in_mask.inputs["Vector"])
        tree.add_link(map_range.outputs[1], in_multi.inputs["Vector"])
        tree.add_link(map_range.outputs[1], in_normal.inputs["Vector"])


@classes.register
class ShaderNodePso2Classic(bpy.types.ShaderNodeCustomGroup):

    bl_name = "ShaderNodePso2Classic"
    bl_label = "PSO2 Classic"
    bl_icon = "NONE"

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.bl_label, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

        self.inputs["Diffuse"].default_value = (1, 0, 1, 1)
        self.inputs["Alpha"].default_value = 1
        self.inputs["Multi RGB"].default_value = (0, 0, 0, 1)

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self):
        tree = builder.NodeTreeBuilder(
            bpy.data.node_groups.new(self.bl_label, "ShaderNodeTree")
        )

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketColor", "Diffuse")
        tree.new_input("NodeSocketFloat", "Alpha")
        tree.new_input("NodeSocketColor", "Multi RGB")
        tree.new_input("NodeSocketFloat", "Multi A")
        tree.new_input("NodeSocketColor", "Normal")

        tree.new_output("NodeSocketShader", "BSDF")
        tree.new_output("NodeSocketFloat", "Skin Mix")

        bsdf = tree.add_node("ShaderNodeBsdfPrincipled")
        tree.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Multi Map ==========

        multi_rgb = tree.add_node("ShaderNodeSeparateColor", name="Multi Map RGB")
        multi_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Multi RGB"], multi_rgb.inputs["Color"])

        # Based on info from Shadowth117
        # R = specular
        # G = skin bleedthrough (handled up a level)
        # B = self illumination (not true emissive)
        # A = environment map bleed through

        # Specular
        spec_inv = tree.add_node("ShaderNodeMapRange", name="Specular to Roughness")
        spec_inv.data_type = "FLOAT"
        spec_inv.interpolation_type = "LINEAR"
        spec_inv.inputs["From Min"].default_value = 0
        spec_inv.inputs["From Max"].default_value = 1
        spec_inv.inputs["To Min"].default_value = 1
        spec_inv.inputs["To Max"].default_value = 0

        tree.add_link(multi_rgb.outputs["Red"], spec_inv.inputs["Value"])
        tree.add_link(spec_inv.outputs["Result"], bsdf.inputs["Roughness"])

        # Skin
        tree.add_link(multi_rgb.outputs["Green"], group_outputs.inputs["Skin Mix"])

        # Emissive
        tree.add_link(multi_rgb.outputs["Blue"], bsdf.inputs["Emission Strength"])
        tree.add_link(group_inputs.outputs["Diffuse"], bsdf.inputs["Emission Color"])

        # Environment map
        # TODO

        # ========== Normal Map ==========

        normal_map = tree.add_node("ShaderNodeNormalMap")

        tree.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        tree.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Base color ==========

        tree.add_link(group_inputs.outputs["Diffuse"], bsdf.inputs["Base Color"])
        tree.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        return tree.tree
