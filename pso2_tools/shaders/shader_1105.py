from . import builder


class Shader1105(builder.ShaderBuilder):
    """NGS eye tear shader"""

    def build(self, context):
        # TODO: figure out how this shader works.
        # For now, make it invisible.
        tree = self.init_tree()

        output = tree.add_node("ShaderNodeOutputMaterial", (6, 0))
        bsdf = tree.add_node("ShaderNodeBsdfTransparent", (0, 0))

        tree.add_link(bsdf.outputs["BSDF"], output.inputs["Surface"])
