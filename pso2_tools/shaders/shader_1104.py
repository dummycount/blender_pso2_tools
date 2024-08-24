import bpy

from .. import classes
from ..colors import ColorId
from . import builder, color_channels, types
from .colorize import ShaderNodePso2Colorize


class Shader1104(builder.ShaderBuilder):
    """NGS eye shader"""

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

        output = tree.add_node("ShaderNodeOutputMaterial", (24, 6))

        shader_group: ShaderNodePso2NgsEye = tree.add_node(
            "ShaderNodePso2NgsEye", (18, 6)
        )
        tree.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 18))
        diffuse.label = "Diffuse"
        diffuse.image = self.textures.default.diffuse

        # Alpha seems to be used for something different than alpha
        # tree.add_link(diffuse.outputs["Alpha"], shader_group.inputs["Alpha"])

        # Color Mask
        mask = tree.add_node("ShaderNodeTexImage", (0, 12))
        mask.label = "Color Mask"
        mask.image = self.textures.default.mask

        colorize: ShaderNodePso2Colorize = tree.add_node(
            "ShaderNodePso2Colorize", (12, 14)
        )

        tree.add_link(diffuse.outputs["Color"], colorize.inputs["Input"])
        tree.add_link(colorize.outputs["Result"], shader_group.inputs["Diffuse"])

        tree.add_link(mask.outputs["Color"], colorize.inputs["Mask RGB"])
        if self.colors.alpha != ColorId.UNUSED:
            tree.add_link(mask.outputs["Alpha"], colorize.inputs["Mask A"])

        channels = tree.add_node("ShaderNodeGroup", (7, 10))
        channels.label = "Colors"
        channels.node_tree = color_channels.get_color_channels_node(context)

        color = ColorId.LEFT_EYE if "eye_l" in self.material.name else ColorId.RIGHT_EYE
        tree.add_color_link(color, channels, colorize.inputs["Color 1"])

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (0, 6))
        multi.label = "Multi Map"
        multi.image = self.textures.default.multi

        tree.add_link(multi.outputs["Color"], shader_group.inputs["Multi RGB"])
        tree.add_link(multi.outputs["Alpha"], shader_group.inputs["Multi A"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (0, 0))
        normal.label = "Normal Map"
        normal.image = self.textures.default.normal

        tree.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])


@classes.register
class ShaderNodePso2NgsEye(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2Eye"
    bl_label = "PSO2 Eye"
    bl_icon = "NONE"

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.name, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

        self.inputs["Diffuse"].default_value = (1, 0, 1, 1)
        self.inputs["Alpha"].default_value = 1
        self.inputs["Multi RGB"].default_value = (0, 1, 1, 1)

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self):
        tree = builder.NodeTreeBuilder(
            bpy.data.node_groups.new(self.name, "ShaderNodeTree")
        )

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketColor", "Diffuse")
        tree.new_input("NodeSocketFloat", "Alpha")
        tree.new_input("NodeSocketColor", "Multi RGB")
        tree.new_input("NodeSocketFloat", "Multi A")
        tree.new_input("NodeSocketColor", "Normal")

        tree.new_output("NodeSocketShader", "BSDF")

        bsdf = tree.add_node("ShaderNodeBsdfPrincipled")
        tree.add_link(bsdf.outputs["BSDF"], group_outputs.inputs["BSDF"])

        # ========== Normal Map ==========

        normal_map = tree.add_node("ShaderNodeNormalMap")

        tree.add_link(group_inputs.outputs["Normal"], normal_map.inputs["Color"])
        tree.add_link(normal_map.outputs[0], bsdf.inputs["Normal"])

        # ========== Multi Map ==========

        # TODO: does this mean the same things as in the default shader?

        multi_rgb = tree.add_node("ShaderNodeSeparateColor")
        multi_rgb.name = "Multi Map RGB"
        multi_rgb.label = multi_rgb.name
        multi_rgb.mode = "RGB"

        tree.add_link(group_inputs.outputs["Multi RGB"], multi_rgb.inputs["Color"])
        tree.add_link(multi_rgb.outputs["Red"], bsdf.inputs["Metallic"])

        # Tone down the shininess a bit to better match in game visuals
        roughness_map = tree.add_node("ShaderNodeMapRange")
        roughness_map.data_type = "FLOAT"
        roughness_map.interpolation_type = "LINEAR"
        roughness_map.clamp = True
        roughness_map.inputs["To Min"].default_value = 0.2
        roughness_map.inputs["To Max"].default_value = 1

        tree.add_link(multi_rgb.outputs["Green"], roughness_map.inputs["Value"])
        tree.add_link(roughness_map.outputs["Result"], bsdf.inputs["Roughness"])

        # Ambient Occlusion
        # (This should really only affect ambient light, but this looks good enough)
        ao = tree.add_node("ShaderNodeMix")
        ao.name = "Ambient Occlusion"
        ao.label = ao.name
        ao.data_type = "RGBA"
        ao.blend_type = "MULTIPLY"
        ao.inputs["Factor"].default_value = 1

        tree.add_link(multi_rgb.outputs["Blue"], ao.inputs["B"])
        tree.add_link(ao.outputs["Result"], bsdf.inputs["Base Color"])

        # Emissive
        tree.add_link(group_inputs.outputs["Multi A"], bsdf.inputs["Emission Strength"])
        tree.add_link(group_inputs.outputs["Diffuse"], bsdf.inputs["Emission Color"])

        # ========== Base color ==========

        tree.add_link(group_inputs.outputs["Diffuse"], ao.inputs["A"])
        tree.add_link(group_inputs.outputs["Alpha"], bsdf.inputs["Alpha"])

        return tree.tree
