from typing import Type, TypeVar, cast

import bpy

_T = TypeVar("_T")


class ShaderNodeCustomGroup(bpy.types.ShaderNodeCustomGroup):
    @property
    def group_name(self):
        return self.bl_label

    def init(self, context):
        if tree := bpy.data.node_groups.get(self.group_name, None):
            self.node_tree = cast(bpy.types.ShaderNodeTree, tree)
        else:
            self.node_tree = cast(
                bpy.types.ShaderNodeTree,
                bpy.data.node_groups.new(self.bl_label, "ShaderNodeTree"),  # type: ignore
            )
            self._build(self.node_tree)

    def free(self):
        if self.node_tree and self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self, node_tree: bpy.types.ShaderNodeTree) -> None:
        raise NotImplementedError()

    def input(self, node_type: Type[_T], name: str) -> _T:
        return cast(_T, self.inputs[name])
