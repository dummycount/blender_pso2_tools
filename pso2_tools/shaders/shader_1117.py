from . import builder, shader_1102


class Shader1117(shader_1102.Shader1102):
    """NGS skin + decal shader"""

    def build(self, context):
        super().build(context)

        tree = builder.NodeTreeBuilder(self.tree)
        frame = tree.tree.nodes["Frame"]
        diffuse = tree.tree.nodes["Skin Colorize"]
        skin = tree.tree.nodes["PSO2 NGS Skin"]

        skin.location.x += 50 * 6

        decal_uv = tree.add_node("ShaderNodeUVMap", (18, -4), name="Decal UV")
        decal_uv.parent = frame
        decal_uv.uv_map = "UVChannel_3"

        decal = tree.add_node("ShaderNodeTexImage", (24, 0), name="Decal")
        decal.parent = frame
        decal.image = self.textures.decal.diffuse
        decal.extension = "CLIP"

        decal_mix = tree.add_node("ShaderNodeMix", (30, 4), name="Decal Mix")
        decal_mix.parent = frame
        decal_mix.data_type = "RGBA"
        decal_mix.blend_type = "MIX"
        decal_mix.clamp_factor = True

        tree.add_link(decal_uv.outputs["UV"], decal.inputs["Vector"])
        tree.add_link(diffuse.outputs["Result"], decal_mix.inputs["A"])
        tree.add_link(decal.outputs["Color"], decal_mix.inputs["B"])
        tree.add_link(decal.outputs["Alpha"], decal_mix.inputs["Factor"])
        tree.add_link(decal_mix.outputs["Result"], skin.inputs["Diffuse"])
