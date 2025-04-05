from typing import cast

import bpy
from bpy.types import Context, UILayout

from .. import classes
from . import builder, group


class ShaderNodePso2Mix(group.ShaderNodeCustomGroup):
    def _build(self, node_tree):
        tree = builder.NodeTreeBuilder(node_tree)

        group_inputs = tree.add_node("NodeGroupInput")
        group_outputs = tree.add_node("NodeGroupOutput")

        self._add_inputs(tree)
        tree.new_input("NodeSocketColor", "Color 1")
        tree.new_input("NodeSocketFloat", "Alpha 1")
        tree.new_input("NodeSocketColor", "Color 2")
        tree.new_input("NodeSocketFloat", "Alpha 2")

        tree.new_output("NodeSocketColor", "Color")
        tree.new_output("NodeSocketFloat", "Alpha")

        color = tree.add_node("ShaderNodeMix", name="Color")
        color.data_type = "RGBA"
        color.blend_type = "MIX"
        color.clamp_factor = True

        alpha = tree.add_node("ShaderNodeMix", name="Alpha")
        alpha.data_type = "FLOAT"
        alpha.blend_type = "MIX"
        alpha.clamp_factor = True

        self._add_nodes(tree)

        tree.add_link(self._factor_socket(node_tree), color.inputs["Factor"])
        tree.add_link(group_inputs.outputs["Color 1"], color.inputs["A"])
        tree.add_link(group_inputs.outputs["Color 2"], color.inputs["B"])

        tree.add_link(self._factor_socket(node_tree), alpha.inputs["Factor"])
        tree.add_link(group_inputs.outputs["Alpha 1"], alpha.inputs["A"])
        tree.add_link(group_inputs.outputs["Alpha 2"], alpha.inputs["B"])

        tree.add_link(color.outputs["Result"], group_outputs.inputs["Color"])
        tree.add_link(alpha.outputs["Result"], group_outputs.inputs["Alpha"])

    def _add_inputs(self, tree: builder.NodeTreeBuilder):
        pass

    def _add_nodes(self, tree: builder.NodeTreeBuilder):
        pass

    def _factor_socket(self, tree: bpy.types.ShaderNodeTree) -> bpy.types.NodeSocket:
        raise NotImplementedError()


@classes.register
class ShaderNodePso2MixTexture(ShaderNodePso2Mix):
    bl_name = "ShaderNodePso2MixTexture"
    bl_label = "PSO2 Mix Texture"
    bl_icon = "NONE"

    def _add_inputs(self, tree: builder.NodeTreeBuilder):
        tree.new_input("NodeSocketFloat", "Factor")

    def _factor_socket(self, tree: bpy.types.ShaderNodeTree):
        return tree.nodes["Group Input"].outputs["Factor"]


@classes.register
class ShaderNodePso2MixTextureAttribute(ShaderNodePso2Mix):
    bl_name = "ShaderNodePso2MixTextureAttribute"
    bl_label = "PSO2 Mix Texture Attribute"
    bl_icon = "NONE"

    has_attributes = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.width = 180

    def _type_update(self, context: bpy.types.Context):
        self.attribute_node.attribute_type = self.attribute_type

    def _name_update(self, context: bpy.types.Context):
        self.attribute_node.attribute_name = self.attribute_name

    attribute_type: bpy.props.EnumProperty(
        name="Type",
        update=_type_update,
        items=[
            ("GEOMETRY", "Geometry", ""),
            ("OBJECT", "Object", ""),
            ("INSTANCE", "Instancer", ""),
            ("VIEW_LAYER", "View Layer", ""),
        ],
    )
    attribute_name: bpy.props.StringProperty(name="Name", update=_name_update)

    def draw_buttons(self, context: Context, layout: UILayout):
        layout.prop(self, "attribute_type")
        layout.prop(self, "attribute_name")

    @property
    def attribute_node(self):
        if not self.node_tree:
            raise RuntimeError("Tree missing")

        return cast(bpy.types.ShaderNodeAttribute, self.node_tree.nodes["Attribute"])

    def _add_nodes(self, tree: builder.NodeTreeBuilder):
        attr = tree.add_node("ShaderNodeAttribute", name="Attribute")
        attr.attribute_type = self.attribute_type
        attr.attribute_name = self.attribute_name

    def _factor_socket(self, tree: bpy.types.ShaderNodeTree):
        return tree.nodes["Attribute"].outputs["Fac"]
