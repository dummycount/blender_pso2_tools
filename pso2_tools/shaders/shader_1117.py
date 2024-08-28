from . import builder, shader_1102


class Shader1117(shader_1102.Shader1102):
    """NGS skin + decal shader"""

    def build(self, context):
        super().build(context)

        tree = builder.NodeTreeBuilder(self.tree)
        frame = tree.tree.nodes["Frame"]
        diffuse = tree.tree.nodes["PSO2 Colorize"]
        skin = tree.tree.nodes["PSO2 NGS Skin"]

        skin.location.x += 50 * 6

        decal_uv = tree.add_node("ShaderNodeUVMap", (18, -4))
        decal_uv.parent = frame
        decal_uv.name = "Decal UV"
        decal_uv.label = decal_uv.name
        decal_uv.uv_map = "UVChannel_3"

        decal = tree.add_node("ShaderNodeTexImage", (24, 0))
        decal.parent = frame
        decal.name = "Decal"
        decal.label = decal.name
        decal.image = self.textures.decal.diffuse
        decal.extension = "CLIP"

        decal_mix = tree.add_node("ShaderNodeMix", (30, 4))
        decal_mix.parent = frame
        decal_mix.name = "Decal Mix"
        decal_mix.label = decal_mix.name
        decal_mix.data_type = "RGBA"
        decal_mix.blend_type = "MIX"
        decal_mix.clamp_factor = True

        tree.add_link(decal_uv.outputs["UV"], decal.inputs["Vector"])
        tree.add_link(diffuse.outputs["Result"], decal_mix.inputs["A"])
        tree.add_link(decal.outputs["Color"], decal_mix.inputs["B"])
        tree.add_link(decal.outputs["Alpha"], decal_mix.inputs["Factor"])
        tree.add_link(decal_mix.outputs["Result"], skin.inputs["Diffuse"])
