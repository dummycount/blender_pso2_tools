import bpy
from pso2_tools import classes
from pso2_tools.colors import MAGENTA
from pso2_tools.shaders import shader


class ShaderNodePso2NgsBasic(bpy.types.ShaderNodeCustomGroup):
    def __init__(self, blend_type: str):
        super().__init__()
        self.blend_type = blend_type
        self.node_tree = None

    def init(self, context):
        self.node_tree = self.build(self.blend_type)

        self.inputs["Diffuse"].default_value = MAGENTA
        self.inputs["Alpha"].default_value = 1

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def build(self, blend_type):
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
        build.new_input("NodeSocketColor", "Color 3")
        build.new_input("NodeSocketColor", "Color 4")
        build.new_input("NodeSocketColor", "Mask RGB")
        build.new_input("NodeSocketFloat", "Mask A")
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
        build.add_link(spec_rgb.outputs["Red"], bsdf.inputs["Metallic"])
        build.add_link(spec_rgb.outputs["Green"], bsdf.inputs["Roughness"])

        # ========== Ambient Occlusion ==========

        # This should really only affect ambient light, but this looks good enough
        ao = build.add_node("ShaderNodeMix")
        ao.name = "Ambient Occlusion"
        ao.label = ao.name
        ao.data_type = "RGBA"
        ao.blend_type = "MULTIPLY"
        ao.inputs["Factor"].default_value = 1

        build.add_link(spec_rgb.outputs["Blue"], ao.inputs["B"])
        build.add_link(ao.outputs["Result"], bsdf.inputs["Base Color"])

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
        color1.name = "Color 1"
        color1.label = color1.name
        color1.data_type = "RGBA"
        color1.blend_type = blend_type
        color1.clamp_factor = True

        color2 = build.add_node("ShaderNodeMix")
        color2.name = "Color 2"
        color2.label = color2.name
        color2.data_type = "RGBA"
        color2.blend_type = blend_type
        color2.clamp_factor = True

        color3 = build.add_node("ShaderNodeMix")
        color3.name = "Color 3"
        color3.label = color3.name
        color3.data_type = "RGBA"
        color3.blend_type = blend_type
        color3.clamp_factor = True

        color4 = build.add_node("ShaderNodeMix")
        color4.name = "Color 4"
        color4.label = color4.name
        color4.data_type = "RGBA"
        color4.blend_type = blend_type
        color4.clamp_factor = True

        build.add_link(multi_rgb.outputs["Red"], color1.inputs["Factor"])
        build.add_link(group_inputs.outputs["Diffuse"], color1.inputs["A"])
        build.add_link(group_inputs.outputs["Color 1"], color1.inputs["B"])

        build.add_link(multi_rgb.outputs["Green"], color2.inputs["Factor"])
        build.add_link(color1.outputs["Result"], color2.inputs["A"])
        build.add_link(group_inputs.outputs["Color 2"], color2.inputs["B"])

        build.add_link(multi_rgb.outputs["Blue"], color3.inputs["Factor"])
        build.add_link(color2.outputs["Result"], color3.inputs["A"])
        build.add_link(group_inputs.outputs["Color 3"], color3.inputs["B"])

        build.add_link(group_inputs.outputs["Mask A"], color4.inputs["Factor"])
        build.add_link(color3.outputs["Result"], color4.inputs["A"])
        build.add_link(group_inputs.outputs["Color 4"], color4.inputs["B"])

        build.add_link(color4.outputs["Result"], ao.inputs["A"])
        build.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        # ========== Emissive Map ==========

        build.add_link(
            group_inputs.outputs["Specular A"], bsdf.inputs["Emission Strength"]
        )
        build.add_link(color4.outputs["Result"], bsdf.inputs["Emission Color"])

        return tree


@classes.register_class
class ShaderNodePso2Ngs(ShaderNodePso2NgsBasic):
    bl_name = "ShaderNodePso2Ngs"
    bl_label = "PSO2 NGS"
    bl_icon = "NONE"

    def __init__(self) -> None:
        super().__init__("MIX")


@classes.register_class
class ShaderNodePso2NgsSkin(ShaderNodePso2NgsBasic):
    bl_name = "ShaderNodePso2NgsSkin"
    bl_label = "PSO2 NGS Skin"
    bl_icon = "NONE"

    def __init__(self):
        super().__init__("MULTIPLY")
