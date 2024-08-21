from typing import Literal, Optional, Tuple, overload

import bpy

from ..colors import ColorId

GRID = 50

Vec2 = Tuple[float, float]
OVec2 = Optional[Vec2]


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

    def new_input(
        self,
        socket_type: str,
        name: str,
        parent: Optional[bpy.types.NodeTreeInterfacePanel] = None,
    ):
        return self.tree.interface.new_socket(
            name=name, in_out="INPUT", socket_type=socket_type, parent=parent
        )

    def new_output(
        self,
        socket_type: str,
        name: str,
        parent: Optional[bpy.types.NodeTreeInterfacePanel] = None,
    ):
        return self.tree.interface.new_socket(
            name=name, in_out="OUTPUT", socket_type=socket_type, parent=parent
        )

    def add_link(
        self, in_socket: bpy.types.NodeSocket, out_socket: bpy.types.NodeSocket
    ) -> bpy.types.NodeLink:
        return self.tree.links.new(in_socket, out_socket)

    def add_color_link(
        self,
        channel: ColorId,
        colors: bpy.types.ShaderNodeGroup,
        output: bpy.types.NodeSocket,
    ):
        if channel == ColorId.UNUSED:
            return None

        return self.tree.links.new(colors.outputs[channel.value - 1], output)

    @overload
    def add_node(
        self, t: Literal["NodeFrame"], loc: OVec2 = None
    ) -> bpy.types.NodeFrame: ...

    @overload
    def add_node(
        self, t: Literal["NodeGroupInput"], loc: OVec2 = None
    ) -> bpy.types.NodeGroupInput: ...

    @overload
    def add_node(
        self, t: Literal["NodeGroupOutput"], loc: OVec2 = None
    ) -> bpy.types.NodeGroupOutput: ...

    @overload
    def add_node(
        self, t: Literal["NodeReroute"], loc: OVec2 = None
    ) -> bpy.types.NodeReroute: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeAttribute"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeAttribute: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeBsdfPrincipled"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeBsdfPrincipled: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeBsdfTransparent"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeBsdfTransparent: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeGroup"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeGroup: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeMath"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeMath: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeMapRange"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeMapRange: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeMix"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeMix: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeMixShader"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeMixShader: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeNormalMap"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeNormalMap: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeOutputMaterial"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeOutputMaterial: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeRGB"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeRGB: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeSeparateColor"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeSeparateColor: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeTexImage"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeTexImage: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeUVMap"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeUVMap: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeValue"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeValue: ...

    @overload
    def add_node(
        self, t: Literal["ShaderNodeVertexColor"], loc: OVec2 = None
    ) -> bpy.types.ShaderNodeVertexColor: ...

    def add_node(self, node_type: str, location: OVec2 = None) -> bpy.types.Node:
        return self._add_node(node_type, location)

    def _add_node(self, node_type: str, location: OVec2):
        x, y = location or (0, 0)

        node = self.tree.nodes.new(node_type)
        node.location = (x * GRID, y * GRID)

        return node

    def add_group(self, name: str, offset: Vec2 = (0, 0)):
        return NodeTreeGroupBuilder(self.tree, name, offset)


class NodeTreeGroupBuilder(NodeTreeBuilder):
    def __init__(self, tree: bpy.types.NodeTree, name: str, offset: Vec2 = (0, 0)):
        super().__init__(tree)
        self.offset = offset

        self.frame = super()._add_node("NodeFrame", offset)
        self.frame.label = name

    def _add_node(self, node_type: str, location: OVec2):
        x, y = location or (0, 0)

        x += self.offset[0]
        y += self.offset[1]

        node = super()._add_node(node_type, (x, y))
        node.parent = self.frame

        return node
