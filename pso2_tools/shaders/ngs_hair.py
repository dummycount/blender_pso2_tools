import bpy

from pso2_tools import classes
from pso2_tools.colors import BLACK, Colors, WHITE, DEFAULT_HAIR_1, DEFAULT_HAIR_2
from pso2_tools.shaders import shader


class NgsHairMaterial(shader.ShaderBuilder):
    textures: shader.MaterialTextures
    colors: list[Colors]

    def __init__(
        self,
        material: bpy.types.Material,
        textures: shader.MaterialTextures,
        colors: list[Colors],
    ):
        super().__init__(material)
        self.textures = textures
        self.colors = colors

    def build(self, context: bpy.types.Context):
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

    def _channel(self, idx: int):
        try:
            return self.colors[idx]
        except IndexError:
            return Colors.Unused


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

        self.inputs["Diffuse"].default_value = WHITE
        self.inputs["Alpha"].default_value = 1
        self.inputs["Color 1"].default_value = DEFAULT_HAIR_1
        self.inputs["Color 2"].default_value = DEFAULT_HAIR_2
        self.inputs["Color 3"].default_value = BLACK
        self.inputs["Color 4"].default_value = BLACK

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

        build.new_input("NodeSocketFloat", "Alpha")
        build.new_input("NodeSocketColor", "Diffuse")
        build.new_input("NodeSocketColor", "Color 1")
        build.new_input("NodeSocketColor", "Color 2")
        build.new_input("NodeSocketColor", "Color 3")
        build.new_input("NodeSocketColor", "Color 4")
        build.new_input("NodeSocketColor", "Mask RGB")
        build.new_input("NodeSocketColor", "Specular RGB")
        build.new_input("NodeSocketFloat", "Specular A")
        build.new_input("NodeSocketColor", "Normal")
        build.new_input("NodeSocketColor", "Texture O")

        build.new_output("NodeSocketShader", "BSDF")

        bsdf = build.add_node("ShaderNodeBsdfPrincipled")
        # bsdf.inputs["Specular"].default_value = 0.03

        build.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Specular Map ==========

        spec_rgb = build.add_node("ShaderNodeSeparateColor")
        spec_rgb.name = "Specular RGB"
        spec_rgb.label = spec_rgb.name
        spec_rgb.mode = "RGB"

        build.add_link(group_inputs.outputs["Specular RGB"], spec_rgb.inputs[0])
        # Are these used at all for hair, or are they just for the parts of the
        # hair model that use the regular shader?
        # build.add_link(spec_rgb.outputs["Red"], ???)
        # build.add_link(spec_rgb.outputs["Green"], ???)
        # build.add_link(spec_rgb.outputs["Blue"], ???)
        # build.add_link(group_inputs.outputs["Specular A"], ???)

        # ========== Normal Map ==========

        normal_map = build.add_node("ShaderNodeNormalMap")

        build.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        build.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Unknown ==========
        # TODO: figure out what texture _o does.

        # ========== Base Color ==========

        multi_rgb = build.add_node("ShaderNodeSeparateColor")
        multi_rgb.name = "Multi Color"
        multi_rgb.label = multi_rgb.name
        multi_rgb.mode = "RGB"

        build.add_link(group_inputs.outputs["Mask RGB"], multi_rgb.inputs["Color"])

        color1 = build.add_node("ShaderNodeMix")
        color1.label = "Color 1"
        color1.data_type = "RGBA"
        color1.blend_type = "MULTIPLY"
        color1.clamp_factor = True

        color2 = build.add_node("ShaderNodeMix")
        color2.label = "Color 2"
        color2.data_type = "RGBA"
        color2.blend_type = "MULTIPLY"
        color2.clamp_factor = True

        build.add_link(multi_rgb.outputs["Red"], color1.inputs["Factor"])
        build.add_link(group_inputs.outputs["Diffuse"], color1.inputs["A"])
        build.add_link(group_inputs.outputs["Color 1"], color1.inputs["B"])

        build.add_link(multi_rgb.outputs["Green"], color2.inputs["Factor"])
        build.add_link(color1.outputs["Result"], color2.inputs["A"])
        build.add_link(group_inputs.outputs["Color 2"], color2.inputs["B"])

        build.add_link(color2.outputs["Result"], bsdf.inputs["Base Color"])
        build.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        return tree
