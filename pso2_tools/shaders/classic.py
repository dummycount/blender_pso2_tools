import bpy
from bpy.types import Material

from pso2_tools import classes
from pso2_tools.shaders import default_colors, shader


def is_classic_shader(name: str):
    try:
        return int(name.split(",")[1]) < 1000
    except (ValueError, IndexError):
        return False


class ClassicDefaultMaterial(shader.ShaderBuilder):
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

        self.inputs["Diffuse"].default_value = default_colors.MAGENTA
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

        tree.inputs.new("NodeSocketColor", "Diffuse")
        tree.inputs.new("NodeSocketFloat", "Alpha")
        tree.inputs.new("NodeSocketColor", "Color 1")
        tree.inputs.new("NodeSocketColor", "Color 2")
        tree.inputs.new("NodeSocketColor", "Mask RGB")
        tree.inputs.new("NodeSocketColor", "Specular RGB")
        tree.inputs.new("NodeSocketFloat", "Specular A")
        tree.inputs.new("NodeSocketColor", "Normal")
        tree.inputs.new("NodeSocketColor", "Texture O")

        tree.outputs.new("NodeSocketShader", "BSDF")

        bsdf = build.add_node("ShaderNodeBsdfPrincipled")
        build.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Specular Map ==========

        spec_rgb = build.add_node("ShaderNodeSeparateRGB")
        spec_rgb.label = "Specular RGB"

        build.add_link(group_inputs.outputs["Specular RGB"], spec_rgb.inputs[0])

        # G channel is skin mask
        # TODO, what are each of R, B, and A used for? Just guessing here.
        build.add_link(spec_rgb.outputs["R"], bsdf.inputs["Specular"])
        build.add_link(spec_rgb.outputs["B"], bsdf.inputs["Metallic"])
        build.add_link(group_inputs.outputs["Specular A"], bsdf.inputs["Clearcoat"])

        # ========== Base Color ==========

        multi_rgb = build.add_node("ShaderNodeSeparateRGB")
        build.add_link(group_inputs.outputs["Mask RGB"], multi_rgb.inputs[0])

        color1 = build.add_node("ShaderNodeMixRGB")
        color1.label = "Color 1"
        color1.blend_type = "MIX"  # Assuming color 1 is always skin?
        color1.use_clamp = True

        color2 = build.add_node("ShaderNodeMixRGB")
        color2.label = "Color 2"
        color2.blend_type = "MIX"
        color2.use_clamp = True

        build.add_link(spec_rgb.outputs["G"], color1.inputs["Fac"])
        build.add_link(group_inputs.outputs["Diffuse"], color1.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 1"], color1.inputs["Color2"])

        build.add_link(multi_rgb.outputs["G"], color2.inputs["Fac"])
        build.add_link(color1.outputs["Color"], color2.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 2"], color2.inputs["Color2"])

        # TODO: R channel appears unused? G and B channels are similar but not the same.

        build.add_link(color2.outputs[0], bsdf.inputs["Base Color"])
        build.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        # ========== Normal Map ==========

        normal_map = build.add_node("ShaderNodeNormalMap")

        build.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        build.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Unknown ==========
        # TODO: figure out what texture _o does.

        return tree
