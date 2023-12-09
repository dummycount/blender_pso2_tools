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

        tree.inputs.new("NodeSocketColor", "Diffuse")
        tree.inputs.new("NodeSocketFloat", "Alpha")
        tree.inputs.new("NodeSocketColor", "Color 1")
        tree.inputs.new("NodeSocketColor", "Color 2")
        tree.inputs.new("NodeSocketColor", "Color 3")
        tree.inputs.new("NodeSocketColor", "Color 4")
        tree.inputs.new("NodeSocketColor", "Mask RGB")
        tree.inputs.new("NodeSocketFloat", "Mask A")
        tree.inputs.new("NodeSocketColor", "Specular RGB")
        tree.inputs.new("NodeSocketFloat", "Specular A")
        tree.inputs.new("NodeSocketColor", "Normal")
        tree.inputs.new("NodeSocketColor", "Texture O")

        tree.outputs.new("NodeSocketShader", "BSDF")

        bsdf = build.add_node("ShaderNodeBsdfPrincipled")
        build.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Base Color ==========

        multi_rgb = build.add_node("ShaderNodeSeparateRGB")
        build.add_link(group_inputs.outputs["Mask RGB"], multi_rgb.inputs[0])

        color1 = build.add_node("ShaderNodeMixRGB")
        color1.label = "Color 1"
        color1.blend_type = blend_type
        color1.use_clamp = True

        color2 = build.add_node("ShaderNodeMixRGB")
        color2.label = "Color 2"
        color2.blend_type = blend_type
        color2.use_clamp = True

        color3 = build.add_node("ShaderNodeMixRGB")
        color3.label = "Color 3"
        color3.blend_type = blend_type
        color3.use_clamp = True

        color4 = build.add_node("ShaderNodeMixRGB")
        color4.label = "Color 4"
        color4.blend_type = blend_type
        color4.use_clamp = True

        build.add_link(multi_rgb.outputs["R"], color1.inputs["Fac"])
        build.add_link(group_inputs.outputs["Diffuse"], color1.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 1"], color1.inputs["Color2"])

        build.add_link(multi_rgb.outputs["G"], color2.inputs["Fac"])
        build.add_link(color1.outputs["Color"], color2.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 2"], color2.inputs["Color2"])

        build.add_link(multi_rgb.outputs["B"], color3.inputs["Fac"])
        build.add_link(color2.outputs["Color"], color3.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 3"], color3.inputs["Color2"])

        build.add_link(group_inputs.outputs["Mask A"], color4.inputs["Fac"])
        build.add_link(color3.outputs["Color"], color4.inputs["Color1"])
        build.add_link(group_inputs.outputs["Color 4"], color4.inputs["Color2"])

        build.add_link(color4.outputs[0], bsdf.inputs["Base Color"])
        build.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        # ========== Specular Map ==========

        spec_rgb = build.add_node("ShaderNodeSeparateRGB")
        spec_rgb.label = "Specular RGB"

        build.add_link(group_inputs.outputs["Specular RGB"], spec_rgb.inputs[0])
        # TODO, what are each of R, G, B, and A used for? Just guessing here.
        build.add_link(spec_rgb.outputs["R"], bsdf.inputs["Metallic"])
        build.add_link(spec_rgb.outputs["G"], bsdf.inputs["Roughness"])
        build.add_link(spec_rgb.outputs["B"], bsdf.inputs["Specular"])
        build.add_link(group_inputs.outputs["Specular A"], bsdf.inputs["Clearcoat"])

        # ========== Normal Map ==========

        normal_map = build.add_node("ShaderNodeNormalMap")

        build.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        build.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Unknown ==========
        # TODO: figure out what texture _o does.

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
