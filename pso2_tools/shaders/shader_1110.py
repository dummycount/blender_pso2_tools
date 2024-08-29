from . import builder, shader_1100


class Shader1110(shader_1100.Shader1100):
    """NGS default + decal shader"""

    def build(self, context):
        super().build(context)

        tree = builder.NodeTreeBuilder(self.tree)
        diffuse = tree.tree.nodes["PSO2 Colorize"]
        shader = tree.tree.nodes["PSO2 NGS"]
        output = tree.tree.nodes["Material Output"]

        shader.location.x += 50 * 6
        output.location.x += 60 * 6

        decal_uv = tree.add_node("ShaderNodeUVMap", (6, 20), name="Decal UV")
        decal_uv.uv_map = "UVChannel_3"

        decal = tree.add_node("ShaderNodeTexImage", (12, 20), name="Decal")
        decal.image = self.textures.decal.diffuse
        decal.extension = "CLIP"

        decal_mix = tree.add_node("ShaderNodeMix", (18, 16), name="Decal Mix")
        decal_mix.data_type = "RGBA"
        decal_mix.blend_type = "MIX"
        decal_mix.clamp_factor = True

        tree.add_link(decal_uv.outputs["UV"], decal.inputs["Vector"])
        tree.add_link(diffuse.outputs["Result"], decal_mix.inputs["A"])
        tree.add_link(decal.outputs["Color"], decal_mix.inputs["B"])
        tree.add_link(decal.outputs["Alpha"], decal_mix.inputs["Factor"])
        tree.add_link(decal_mix.outputs["Result"], shader.inputs["Diffuse"])
