import bpy

from .. import classes, scene_props
from . import builder


@classes.register
class ShaderNodePso2ShowInnerwear(bpy.types.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2ShowInnerwear"
    bl_label = "PSO2 Show Innerwear"
    bl_icon = "NONE"

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.bl_label, None):
            self.node_tree = tree
        else:
            self.node_tree = self._build()

        self.inputs["Value"].default_value = 1

    def free(self):
        if self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self):
        tree = builder.NodeTreeBuilder(
            bpy.data.node_groups.new(self.bl_label, "ShaderNodeTree")
        )

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketFloat", "Value")

        tree.new_output("NodeSocketFloat", "Value")

        in_hide = tree.add_node("ShaderNodeAttribute", name="Hide Innerwear")
        in_hide.attribute_type = "VIEW_LAYER"
        in_hide.attribute_name = scene_props.HIDE_INNERWEAR

        in_show = tree.add_node("ShaderNodeMath", name="Show Innerwear")
        in_show.operation = "SUBTRACT"
        in_show.inputs[0].default_value = 1

        tree.add_link(in_hide.outputs["Fac"], in_show.inputs[1])

        multiply = tree.add_node("ShaderNodeMath")
        multiply.operation = "MULTIPLY"
        multiply.use_clamp = True

        tree.add_link(in_show.outputs[0], multiply.inputs[0])
        tree.add_link(group_inputs.outputs["Value"], multiply.inputs[1])

        tree.add_link(multiply.outputs[0], group_outputs.inputs["Value"])

        return tree.tree
