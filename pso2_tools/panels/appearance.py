import re

import bpy

from .. import classes, colors, material, scene_props

MAT_RE = re.compile(r"^\(\d+p,\d+\)")


@classes.register
class PSO2AppearancePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pso2_appearance"
    bl_label = "PSO2 Appearance"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return any(mat for mat in bpy.data.materials if MAT_RE.match(mat.name))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.scene, scene_props.HIDE_INNERWEAR)
        layout.prop(context.scene, scene_props.MUSCULARITY)

        header, body = layout.panel("PSO2_appearance_colors", default_closed=True)
        header.label(text="Colors", icon="COLOR")
        if body:
            body.use_property_split = False

            grid = body.grid_flow(columns=3)

            for channel in colors.COLOR_CHANNELS.values():
                grid.prop(context.scene, channel.custom_property_name)


@classes.register
class PSO2MaterialPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pso2_material"
    bl_label = "PSO2 Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        # Show only for materials whose names match the expected form
        return bool(
            context.material and material.FBX_MATERIAL_RE.match(context.material.name)
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.material, scene_props.ALPHA_THRESHOLD)
