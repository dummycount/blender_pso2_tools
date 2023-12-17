import bpy

from pso2_tools import classes
from pso2_tools.colors import Colors, MAGENTA
from pso2_tools.shaders import shader


def is_classic_shader(name: str):
    try:
        return int(name.split(",")[1]) < 1000
    except (ValueError, IndexError):
        return False


class ClassicDefaultMaterial(shader.ShaderBuilder):
    textures: shader.MaterialTextures

    def __init__(
        self,
        material: bpy.types.Material,
        textures: shader.MaterialTextures,
    ):
        super().__init__(material)
        self.textures = textures

    def build(self, context: bpy.types.Context):
        build = self.init_tree()

        shader_group: ShaderNodePso2ClassicOutfit = build.add_node(
            "ShaderNodePso2ClassicOutfit", (12, 9)
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
        colors.label = "Colors"
        colors.node_tree = shader.get_color_channels_node(context)

        # TODO: handle cast part colors?
        build.add_color_link(Colors.MainSkin, colors, shader_group.inputs["Color 1"])
        build.add_color_link(Colors.Base1, colors, shader_group.inputs["Color 2"])

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
        texture_l = build.add_node("ShaderNodeTexImage", (0, -12))
        texture_l.label = "Texture L"
        texture_l.image = self.textures.layer

        build.add_link(texture_l.outputs["Color"], shader_group.inputs["Texture O"])

        # Unknown
        texture_o = build.add_node("ShaderNodeTexImage", (0, -18))
        texture_o.label = "Texture O"
        texture_o.image = self.textures.texture_o

        build.add_link(texture_o.outputs["Color"], shader_group.inputs["Texture O"])

        # TODO: handle innerwear


@classes.register_class
class ShaderNodePso2ClassicOutfit(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2ClassicOutfit"
    bl_label = "PSO2 Classic Outfit"
    bl_icon = "NONE"

    def __init__(self):
        super().__init__()
        self.node_tree = None

    def init(self, context):
        self.node_tree = self.build()

        self.inputs["Diffuse"].default_value = MAGENTA
        self.inputs["Alpha"].default_value = 1

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def build(self):
        if tree := bpy.data.node_groups.get(self.name, None):
            return tree

        tree = bpy.data.node_groups.new(self.name, "ShaderNodeTree")
        build = shader.NodeTreeBuilder(tree)

        group_inputs = build.add_node("NodeGroupInput")
        group_outputs = build.add_node("NodeGroupOutput")

        build.new_input("NodeSocketColor", "Diffuse")
        build.new_input("NodeSocketFloat", "Alpha")
        build.new_input("NodeSocketColor", "Color 1")
        build.new_input("NodeSocketColor", "Color 2")
        build.new_input("NodeSocketColor", "Mask RGB")
        build.new_input("NodeSocketColor", "Specular RGB")
        build.new_input("NodeSocketFloat", "Specular A")
        build.new_input("NodeSocketColor", "Normal")
        build.new_input("NodeSocketColor", "Texture O")

        build.new_output("NodeSocketShader", "BSDF")

        bsdf = build.add_node("ShaderNodeBsdfPrincipled")
        build.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Specular Map ==========

        spec_rgb = build.add_node("ShaderNodeSeparateColor")
        spec_rgb.name = "Specular RGB"
        spec_rgb.label = spec_rgb.name
        spec_rgb.mode = "RGB"

        build.add_link(group_inputs.outputs["Specular RGB"], spec_rgb.inputs["Color"])

        # G channel is skin mask
        # TODO, what are each of R, B, and A used for? Just guessing here.
        # R seems to be some sort of shading value? Most is 50% gray, and some
        # regions are brighter or darker.

        # build.add_link(spec_rgb.outputs["Red"], ???)
        build.add_link(spec_rgb.outputs["Blue"], bsdf.inputs["Metallic"])

        # A seems to be shininess?
        spec_a_inv = build.add_node("ShaderNodeMapRange")
        spec_a_inv.name = "Invert Specular A"
        spec_a_inv.label = spec_a_inv.name
        spec_a_inv.data_type = "FLOAT"
        spec_a_inv.interpolation_type = "LINEAR"
        spec_a_inv.inputs["From Min"].default_value = 0
        spec_a_inv.inputs["From Max"].default_value = 1
        spec_a_inv.inputs["To Min"].default_value = 1
        spec_a_inv.inputs["To Max"].default_value = 0

        build.add_link(group_inputs.outputs["Specular A"], spec_a_inv.inputs["Value"])
        build.add_link(spec_a_inv.outputs["Result"], bsdf.inputs["Roughness"])

        # ========== Base Color ==========

        multi_rgb = build.add_node("ShaderNodeSeparateColor")
        multi_rgb.name = "Multi Color"
        multi_rgb.label = multi_rgb.name
        multi_rgb.mode = "RGB"

        build.add_link(group_inputs.outputs["Mask RGB"], multi_rgb.inputs["Color"])

        color1 = build.add_node("ShaderNodeMix")
        color1.label = "Color 1"
        color1.data_type = "RGBA"
        color1.blend_type = "MIX"  # Assuming color 1 is always skin?
        color1.clamp_factor = True

        color2 = build.add_node("ShaderNodeMix")
        color2.label = "Color 2"
        color2.data_type = "RGBA"
        color2.blend_type = "MIX"
        color2.clamp_factor = True

        build.add_link(spec_rgb.outputs["Green"], color1.inputs["Factor"])
        build.add_link(group_inputs.outputs["Diffuse"], color1.inputs["A"])
        build.add_link(group_inputs.outputs["Color 1"], color1.inputs["B"])

        build.add_link(multi_rgb.outputs["Green"], color2.inputs["Factor"])
        build.add_link(color1.outputs["Result"], color2.inputs["A"])
        build.add_link(group_inputs.outputs["Color 2"], color2.inputs["B"])

        # TODO: R channel appears unused? G and B channels are similar but not the same.

        build.add_link(color2.outputs["Result"], bsdf.inputs["Base Color"])
        build.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        # ========== Normal Map ==========

        normal_map = build.add_node("ShaderNodeNormalMap")

        build.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        build.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Unknown ==========
        # TODO: figure out what texture _o does.

        return tree
