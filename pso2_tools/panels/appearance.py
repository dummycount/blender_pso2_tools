import bpy

from .. import classes, colors, scene_props


@classes.register
class PSO2OrnamentsPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pso2_appearance"
    bl_label = "PSO2 Appearance"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return hasattr(bpy.types.Scene, scene_props.HIDE_INNERWEAR)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.scene, scene_props.HIDE_INNERWEAR)
        layout.prop(context.scene, scene_props.MUSCULARITY)

        box = layout.box()
        box.use_property_split = False
        box.label(text="Colors", icon="COLOR")

        grid = box.grid_flow(columns=3)

        for channel in colors.COLOR_CHANNELS.values():
            grid.prop(context.scene, channel.custom_property_name)
