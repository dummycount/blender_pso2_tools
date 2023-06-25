import bpy
from bpy.types import Material

from pso2_tools import classes
from pso2_tools.shaders import default_colors, shader


class NgsHairMaterial(shader.ShaderBuilder):
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

        shader_group: ShaderNodePso2NgsHair = build.add_node(
            "ShaderNodePso2NgsHair", (12, 9)
        )

        output = build.add_node("ShaderNodeOutputMaterial", (18, 9))
        build.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Alpha
        alpha = build.add_node("ShaderNodeTexImage", (0, 18))
        alpha.label = "Alpha"
        alpha.image = self.textures.alpha
        build.add_link(alpha.outputs["Color"], shader_group.inputs["Alpha"])

        # Non-alpha Texture UVs
        uv = build.add_node("ShaderNodeUVMap", (-12, 0))
        uv.label = "UVs"
        uv.uv_map = "UVChannel_2"

        # Base Color
        diffuse = build.add_node("ShaderNodeTexImage", (0, 12))
        diffuse.label = "Diffuse"
        diffuse.image = self.textures.diffuse

        build.add_link(uv.outputs[0], diffuse.inputs["Vector"])
        # Diffuse for hair is typically just white, but some models have black
        # and things break. Can connect this node manually if needed.
        # build.add_link(diffuse.outputs["Color"], shader_group.inputs["Diffuse"])

        # Custom Colors
        multi = build.add_node("ShaderNodeTexImage", (0, 6))
        multi.label = "Multi Color"
        multi.image = self.textures.multi

        build.add_link(uv.outputs[0], multi.inputs["Vector"])
        build.add_link(multi.outputs["Color"], shader_group.inputs["Mask RGB"])

        colors = build.add_node("ShaderNodeGroup", (6, 8))
        colors.label = "Hair Colors"
        colors.node_tree = shader.get_custom_color_group(self.colors)

        build.add_link(colors.outputs[0], shader_group.inputs["Color 1"])
        build.add_link(colors.outputs[1], shader_group.inputs["Color 2"])

        # Specular Map
        specular = build.add_node("ShaderNodeTexImage", (0, 0))
        specular.label = "Specular"
        specular.image = self.textures.specular

        build.add_link(uv.outputs[0], specular.inputs["Vector"])
        build.add_link(specular.outputs["Color"], shader_group.inputs["Specular RGB"])

        # Normal Map
        normal = build.add_node("ShaderNodeTexImage", (0, -6))
        normal.label = "Normal"
        normal.image = self.textures.normal

        build.add_link(uv.outputs[0], normal.inputs["Vector"])
        build.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])

        # Unknown
        texture_o = build.add_node("ShaderNodeTexImage", (0, -12))
        texture_o.label = "Texture O"
        texture_o.image = self.textures.texture_o

        build.add_link(uv.outputs[0], texture_o.inputs["Vector"])
        build.add_link(texture_o.outputs["Color"], shader_group.inputs["Texture O"])


@classes.register_class
class ShaderNodePso2NgsHair(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2NgsHair"
    bl_label = "PSO2 NGS Hair"
    bl_icon = "NONE"

    def __init__(self):
        super().__init__()
        self.node_tree = None

    def init(self, context):
        self.node_tree = self.build()

        self.inputs["Diffuse"].default_value = default_colors.WHITE
        self.inputs["Alpha"].default_value = 1
        self.inputs["Color 1"].default_value = default_colors.HAIR_COLOR_1
        self.inputs["Color 2"].default_value = default_colors.HAIR_COLOR_2

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

        tree.inputs.new("NodeSocketFloat", "Alpha")
        tree.inputs.new("NodeSocketColor", "Diffuse")
        tree.inputs.new("NodeSocketColor", "Color 1")
        tree.inputs.new("NodeSocketColor", "Color 2")
        tree.inputs.new("NodeSocketColor", "Mask RGB")
        tree.inputs.new("NodeSocketColor", "Specular RGB")
        tree.inputs.new("NodeSocketFloat", "Specular A")
        tree.inputs.new("NodeSocketColor", "Normal")
        tree.inputs.new("NodeSocketColor", "Texture O")

        tree.outputs.new("NodeSocketShader", "BSDF")

        bsdf = build.add_node("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Specular"].default_value = 0.03

        build.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Base Color ==========

        multi_rgb = build.add_node("ShaderNodeSeparateRGB")
        build.add_link(group_inputs.outputs["Mask RGB"], multi_rgb.inputs[0])

        color1 = build.add_node("ShaderNodeMixRGB")
        color1.label = "Color 1"
        color1.blend_type = "MULTIPLY"
        color1.use_clamp = True

        color2 = build.add_node("ShaderNodeMixRGB")
        color2.label = "Color 2"
        color2.blend_type = "MULTIPLY"
        color2.use_clamp = True

        build.add_link(multi_rgb.outputs["R"], color1.inputs["Fac"])
        build.add_link(group_inputs.outputs["Diffuse"], color1.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 1"], color1.inputs["Color2"])

        build.add_link(multi_rgb.outputs["G"], color2.inputs["Fac"])
        build.add_link(color1.outputs["Color"], color2.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 2"], color2.inputs["Color2"])

        build.add_link(color2.outputs[0], bsdf.inputs["Base Color"])
        build.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        # ========== Specular Map ==========

        spec_rgb = build.add_node("ShaderNodeSeparateRGB")
        spec_rgb.label = "Specular RGB"

        build.add_link(group_inputs.outputs["Specular RGB"], spec_rgb.inputs[0])
        # TODO, what are each of R, G, B, and A used for? Just guessing here.
        # build.add_link(spec_rgb.outputs["R"], bsdf.inputs["Metallic"])
        # build.add_link(spec_rgb.outputs["G"], bsdf.inputs["Specular"])
        # build.add_link(spec_rgb.outputs["B"], bsdf.inputs["Specular"])
        build.add_link(group_inputs.outputs["Specular A"], bsdf.inputs["Clearcoat"])

        # ========== Normal Map ==========

        normal_map = build.add_node("ShaderNodeNormalMap")

        build.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        build.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Unknown ==========
        # TODO: figure out what texture _o does.

        return tree
