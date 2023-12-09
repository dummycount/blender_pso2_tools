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

from pso2_tools.colors import COLOR_CHANNELS, Colors
from pso2_tools.preferences import get_preferences


GRID = 50


Vec2 = Tuple[float, float]
OVec2 = Optional[Vec2]


_COLOR_GROUP_NAME = "PSO2 Colors"
_COLOR_GROUP_COLS = 6


def get_color_channels_node(context: bpy.types.Context) -> bpy.types.ShaderNodeTree:
    """
    Get a node group for PSO2 color channels.
    """
    if tree := bpy.data.node_groups.get(_COLOR_GROUP_NAME, None):
        return tree

    prefs = get_preferences(context)
    tree = bpy.data.node_groups.new(_COLOR_GROUP_NAME, "ShaderNodeTree")
    builder = NodeTreeBuilder(tree)

    output = builder.add_node("NodeGroupOutput", (28, 0))

    for i, channel in COLOR_CHANNELS.items():
        index = i.value - 1
        x = (index % _COLOR_GROUP_COLS) * 4
        y = (index // _COLOR_GROUP_COLS) * -4

        color = builder.add_node("ShaderNodeRGB", (x, y))
        color.label = channel.name
        color.outputs[0].default_value = getattr(prefs, channel.prop)

        tree.outputs.new("NodeSocketColor", color.label)
        tree.links.new(color.outputs[0], output.inputs[index])

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

    def build(self, context: bpy.types.Context):
        raise NotImplementedError()


class NodeTreeBuilder:
    tree: bpy.types.NodeTree

    def __init__(self, tree: bpy.types.NodeTree):
        self.tree = tree

    def add_link(
        self, input: bpy.types.NodeSocket, output: bpy.types.NodeSocket
    ) -> bpy.types.NodeLink:
        return self.tree.links.new(input, output)

    def add_color_link(
        self,
        channel: Colors,
        colors: bpy.types.ShaderNodeGroup,
        output: bpy.types.NodeSocket,
    ):
        if channel == Colors.Unused:
            return

        return self.tree.links.new(colors.outputs[channel.value - 1], output)

    @overload
    def add_node(self, t: Literal["NodeFrame"], loc: OVec2) -> NodeFrame:
        ...

    @overload
    def add_node(self, t: Literal["NodeGroupInput"], loc: OVec2) -> NodeGroupInput:
        ...

    @overload
    def add_node(self, t: Literal["NodeGroupOutput"], loc: OVec2) -> NodeGroupOutput:
        ...

    @overload
    def add_node(self, t: Literal["NodeReroute"], loc: OVec2) -> NodeReroute:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeBsdfPrincipled"], loc: OVec2
    ) -> ShaderNodeBsdfPrincipled:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeBsdfTransparent"], loc: OVec2
    ) -> ShaderNodeBsdfTransparent:
        ...

    @overload
    def add_node(self, t: Literal["ShaderNodeGroup"], loc: OVec2) -> ShaderNodeGroup:
        ...

    @overload
    def add_node(self, t: Literal["ShaderNodeMath"], loc: OVec2) -> ShaderNodeMath:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeMapRange"], loc: OVec2
    ) -> ShaderNodeMapRange:
        ...

    @overload
    def add_node(self, t: Literal["ShaderNodeMixRGB"], loc: OVec2) -> ShaderNodeMixRGB:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeMixShader"], loc: OVec2
    ) -> ShaderNodeMixShader:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeNormalMap"], loc: OVec2
    ) -> ShaderNodeNormalMap:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeOutputMaterial"], loc: OVec2
    ) -> ShaderNodeOutputMaterial:
        ...

    @overload
    def add_node(self, t: Literal["ShaderNodeRGB"], loc: OVec2) -> ShaderNodeRGB:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeSeparateRGB"], loc: OVec2
    ) -> ShaderNodeSeparateRGB:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeTexImage"], loc: OVec2
    ) -> ShaderNodeTexImage:
        ...

    @overload
    def add_node(self, t: Literal["ShaderNodeUVMap"], loc: OVec2) -> ShaderNodeUVMap:
        ...

    @overload
    def add_node(self, t: Literal["ShaderNodeValue"], loc: OVec2) -> ShaderNodeValue:
        ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeVertexColor"], loc: OVec2
    ) -> ShaderNodeVertexColor:
        ...

    def add_node(
        self, node_type: str, location: Optional[Vec2] = (0, 0)
    ) -> bpy.types.Node:
        node = self.tree.nodes.new(node_type)
        node.location = (location[0] * GRID, location[1] * GRID)
        return node
