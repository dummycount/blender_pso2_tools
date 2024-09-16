from . import attributes, builder
from .ngs import ShaderNodePso2Ngs


class Shader1101(builder.ShaderBuilder):
    """NGS horn/tooth shader"""

    @property
    def textures(self):
        return self.data.textures

    def build(self, context):
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (18, 6))

        shader_group: ShaderNodePso2Ngs = tree.add_node("ShaderNodePso2Ngs", (12, 6))  # type: ignore
        attributes.add_alpha_threshold(
            target=shader_group.inputs["Alpha Threshold"],
            material=self.material,
        )

        tree.add_link(shader_group.outputs["BSDF"], output.inputs["Surface"])

        # Diffuse
        diffuse = tree.add_node("ShaderNodeTexImage", (0, 12), name="Diffuse")
        diffuse.image = self.textures.default.diffuse

        tree.add_link(diffuse.outputs["Color"], shader_group.inputs["Diffuse"])
        tree.add_link(diffuse.outputs["Alpha"], shader_group.inputs["Alpha"])

        # Multi Map
        multi = tree.add_node("ShaderNodeTexImage", (0, 6), name="Multi Map")
        multi.image = self.textures.default.multi

        tree.add_link(multi.outputs["Color"], shader_group.inputs["Multi RGB"])
        tree.add_link(multi.outputs["Alpha"], shader_group.inputs["Multi A"])

        # Normal Map
        normal = tree.add_node("ShaderNodeTexImage", (0, 0), name="Normal Map")
        normal.image = self.textures.default.normal

        tree.add_link(normal.outputs["Color"], shader_group.inputs["Normal"])
