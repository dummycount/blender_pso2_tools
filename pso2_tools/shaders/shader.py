from dataclasses import dataclass
from typing import Literal, Optional, Tuple, overload
import bpy
from bpy.types import (
    NodeFrame,
    NodeGroupInput,
    NodeGroupOutput,
    NodeReroute,
    ShaderNodeBsdfPrincipled,
    ShaderNodeBsdfTransparent,
    ShaderNodeGroup,
    ShaderNodeMixRGB,
    ShaderNodeNormalMap,
    ShaderNodeOutputMaterial,
    ShaderNodeRGB,
    ShaderNodeMapRange,
    ShaderNodeMath,
    ShaderNodeMixShader,
    ShaderNodeSeparateRGB,
    ShaderNodeTexImage,
    ShaderNodeUVMap,
    ShaderNodeValue,
    ShaderNodeVertexColor,
)

GRID = 50


Color = Tuple[float, float, float, float]
Vec2 = Tuple[float, float]
OVec2 = Optional[Vec2]


@dataclass
class ColorGroup:
    name: str
    colors: list[Tuple[str, Color]]


def get_custom_color_group(group: ColorGroup) -> bpy.types.ShaderNodeTree:
    """
    Get a node group for a set of custom colors.

    If a node group with the given name has already been created, this returns it.
    Otherwise, it creates one with the given default colors.

    :param name: The group name.
    :param colors: A list of (name, default_color) tuples.
    """
    if tree := bpy.data.node_groups.get(group.name, None):
        return tree

    tree = bpy.data.node_groups.new(group.name, "ShaderNodeTree")
    builder = NodeTreeBuilder(tree)

    output = builder.add_node("NodeGroupOutput", (6, 0))

    for i, item in enumerate(group.colors):
        label, default_color = item
        color = builder.add_node("ShaderNodeRGB", (0, i * -4))
        color.label = label
        color.outputs[0].default_value = default_color

        tree.outputs.new("NodeSocketColor", label)
        tree.links.new(color.outputs[0], output.inputs[i])

    return tree


@dataclass
class MaterialTextures:
    alpha: Optional[bpy.types.Image] = None  # a
    diffuse: Optional[bpy.types.Image] = None  # d
    layer: Optional[bpy.types.Image] = None  # l
    multi: Optional[bpy.types.Image] = None  # m
    normal: Optional[bpy.types.Image] = None  # n
    specular: Optional[bpy.types.Image] = None  # s
    # Not sure what these are yet
    texture_c: Optional[bpy.types.Image] = None  # c
    texture_g: Optional[bpy.types.Image] = None  # g
    texture_o: Optional[bpy.types.Image] = None  # o
    texture_p: Optional[bpy.types.Image] = None  # p
    texture_v: Optional[bpy.types.Image] = None  # v


class ShaderBuilder:
    material: bpy.types.Material

    def __init__(self, material: bpy.types.Material):
        self.material = material

    @property
    def tree(self):
        return self.material.node_tree

    def init_tree(self):
        self.material.use_nodes = True
        self.tree.nodes.clear()

        return NodeTreeBuilder(self.tree)

    def build(self):
        raise NotImplementedError()


class NodeTreeBuilder:
    tree: bpy.types.NodeTree

    def __init__(self, tree: bpy.types.NodeTree):
        self.tree = tree

    def add_link(
        self, input: bpy.types.NodeSocket, output: bpy.types.NodeSocket
    ) -> bpy.types.NodeLink:

        return self.tree.links.new(input, output)

    @overload
    def add_node(s, t: Literal["NodeFrame"], loc: OVec2) -> NodeFrame:
        ...

    @overload
    def add_node(s, t: Literal["NodeGroupInput"], loc: OVec2) -> NodeGroupInput:
        ...

    @overload
    def add_node(s, t: Literal["NodeGroupOutput"], loc: OVec2) -> NodeGroupOutput:
        ...

    @overload
    def add_node(s, t: Literal["NodeReroute"], loc: OVec2) -> NodeReroute:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeBsdfPrincipled"], loc: OVec2
    ) -> ShaderNodeBsdfPrincipled:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeBsdfTransparent"], loc: OVec2
    ) -> ShaderNodeBsdfTransparent:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeGroup"], loc: OVec2) -> ShaderNodeGroup:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeMath"], loc: OVec2) -> ShaderNodeMath:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeMapRange"], loc: OVec2) -> ShaderNodeMapRange:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeMixRGB"], loc: OVec2) -> ShaderNodeMixRGB:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeMixShader"], loc: OVec2
    ) -> ShaderNodeMixShader:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeNormalMap"], loc: OVec2
    ) -> ShaderNodeNormalMap:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeOutputMaterial"], loc: OVec2
    ) -> ShaderNodeOutputMaterial:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeRGB"], loc: OVec2) -> ShaderNodeRGB:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeSeparateRGB"], loc: OVec2
    ) -> ShaderNodeSeparateRGB:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeTexImage"], loc: OVec2) -> ShaderNodeTexImage:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeUVMap"], loc: OVec2) -> ShaderNodeUVMap:
        ...

    @overload
    def add_node(s, t: Literal["ShaderNodeValue"], loc: OVec2) -> ShaderNodeValue:
        ...

    @overload
    def add_node(
        s, t: Literal["ShaderNodeVertexColor"], loc: OVec2
    ) -> ShaderNodeVertexColor:
        ...

    def add_node(self, type: str, location: Optional[Vec2] = (0, 0)) -> bpy.types.Node:
        node = self.tree.nodes.new(type)
        node.location = (location[0] * GRID, location[1] * GRID)
        return node
