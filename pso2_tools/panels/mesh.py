import bpy

from .. import classes, parts, scene_props


@classes.register
class PSO2MeshIdPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pso2_mesh_id"
    bl_label = "PSO2 Mesh"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return (
            context.object is not None
            and context.object.type == "MESH"
            and parts.get_mesh_id(context.object.name) is not None
        )

    def draw(self, context):
        assert self.layout is not None

        layout = self.layout

        layout.prop(context.object, scene_props.MESH_ID)
