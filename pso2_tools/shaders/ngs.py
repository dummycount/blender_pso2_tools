import bpy

from .. import classes
from . import builder


class ShaderNodePso2NgsBase(bpy.types.ShaderNodeCustomGroup):
    def init(self, context):
        if tree := bpy.data.node_groups.get(self.name, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

        self.inputs["Diffuse"].default_value = (1, 0, 1, 1)
        self.inputs["Alpha"].default_value = 1

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


@classes.register
class ShaderNodePso2Ngs(ShaderNodePso2NgsBase):
    bl_name = "ShaderNodePso2Ngs"
    bl_label = "PSO2 NGS"
    bl_icon = "NONE"


@classes.register
class ShaderNodePso2NgsSkin(ShaderNodePso2NgsBase):
    bl_name = "ShaderNodePso2NgsSkin"
    bl_label = "PSO2 NGS Skin"
    bl_icon = "NONE"

    def _build(self):
        tree = super()._build()
        bsdf = tree.nodes["Principled BSDF"]

        bsdf.subsurface_method = "RANDOM_WALK_SKIN"
        bsdf.inputs["Subsurface Weight"].default_value = 0.2

        return tree
