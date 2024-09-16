from typing import ClassVar, Type, TypeVar, cast

import bpy

_T = TypeVar("_T")


class ShaderNodeCustomGroup(bpy.types.ShaderNodeCustomGroup):
    # Set to True to not share node tree between instances
    has_attributes: ClassVar[bool] = False

    @property
    def group_name(self):
        if self.has_attributes:
            return "." + self.bl_label + "." + self.name

        return self.bl_label

    def init(self, context):
        if not self.has_attributes and (
            tree := bpy.data.node_groups.get(self.group_name, None)
        ):
            self.node_tree = cast(bpy.types.ShaderNodeTree, tree)
        else:
            self.node_tree = cast(
                bpy.types.ShaderNodeTree,
                bpy.data.node_groups.new(self.group_name, "ShaderNodeTree"),  # type: ignore
            )
            self._build(self.node_tree)

    def free(self):
        if self.node_tree and self.node_tree.users == 1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    def _build(self, node_tree: bpy.types.ShaderNodeTree) -> None:
        raise NotImplementedError()

    def input(self, node_type: Type[_T], name: str) -> _T:
        return cast(_T, self.inputs[name])
