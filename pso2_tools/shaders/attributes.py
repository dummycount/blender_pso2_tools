import bpy

from .. import classes, scene_props
from . import builder, group


def add_alpha_threshold(target: bpy.types.NodeSocket, material: bpy.types.Material):
    builder.add_driver(
        target=target,
        prop="default_value",
        id_type="MATERIAL",
        source=material,
        data_path=scene_props.ALPHA_THRESHOLD,
        expression=f"{scene_props.ALPHA_THRESHOLD} / 255",
    )


@classes.register
class ShaderNodePso2ShowInnerwear(group.ShaderNodeCustomGroup):
    bl_name = "ShaderNodePso2ShowInnerwear"
    bl_label = "PSO2 Show Innerwear"
    bl_icon = "NONE"

    def init(self, context):
        super().init(context)

        self.input(bpy.types.NodeSocketFloat, "Value").default_value = 1

    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        tree.new_input("NodeSocketFloat", "Value")

        tree.new_output("NodeSocketFloat", "Value")

        in_hide = tree.add_node("ShaderNodeAttribute", name="Hide Innerwear")
        in_hide.attribute_type = "VIEW_LAYER"
        in_hide.attribute_name = scene_props.HIDE_INNERWEAR

        in_show = tree.add_node("ShaderNodeMath", name="Show Innerwear")
        in_show.operation = "SUBTRACT"
        in_show.inputs[0].default_value = 1  # type: ignore

        tree.add_link(in_hide.outputs["Fac"], in_show.inputs[1])

        multiply = tree.add_node("ShaderNodeMath")
        multiply.operation = "MULTIPLY"
        multiply.use_clamp = True

        tree.add_link(in_show.outputs[0], multiply.inputs[0])
        tree.add_link(group_inputs.outputs["Value"], multiply.inputs[1])

        tree.add_link(multiply.outputs[0], group_outputs.inputs["Value"])
