import re

import bpy

from . import classes, util


@classes.register
class PSO2OrnamentsPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pso2_ornaments"
    bl_label = "PSO2 Ornaments"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentBasewear1.bl_idname)
        row.operator(PSO2_OT_HideOrnamentBasewear1.bl_idname)

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentBasewear2.bl_idname)
        row.operator(PSO2_OT_HideOrnamentBasewear2.bl_idname)

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentOuterwear.bl_idname)
        row.operator(PSO2_OT_HideOrnamentOuterwear.bl_idname)

        layout.separator()

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentHair.bl_idname)
        row.operator(PSO2_OT_HideOrnamentHair.bl_idname)

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentCastBody.bl_idname)
        row.operator(PSO2_OT_HideOrnamentCastBody.bl_idname)

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentCastArm.bl_idname)
        row.operator(PSO2_OT_HideOrnamentCastArm.bl_idname)

        row = layout.row()
        row.operator(PSO2_OT_ShowOrnamentCastLeg.bl_idname)
        row.operator(PSO2_OT_HideOrnamentCastLeg.bl_idname)


MESH_ID_RE = re.compile(r"#(\d+)$")


def get_ornament_mesh_objects(mesh_id: int):
    mesh_id_str = str(mesh_id)

    return [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and (m := MESH_ID_RE.search(util.remove_blender_suffix(obj.name)))
        and m.group(1) == mesh_id_str
    ]


def find_context_area():
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            return area

    return None


class PSO2_OT_ShowOrnament(bpy.types.Operator):
    mesh_id = 0

    def execute(self, context):
        for mesh in get_ornament_mesh_objects(self.mesh_id):
            mesh.hide_set(False)

        return {"FINISHED"}


class PSO2_OT_HideOrnament(bpy.types.Operator):
    mesh_id = 0

    def execute(self, context):

        for mesh in get_ornament_mesh_objects(self.mesh_id):
            mesh.hide_set(True)

        return {"FINISHED"}


@classes.register
class PSO2_OT_ShowOrnamentBasewear1(PSO2_OT_ShowOrnament):
    bl_label = "Show Basewear 1"
    bl_idname = "pso2.show_basewear_ornament_1"
    mesh_id = 3


@classes.register
class PSO2_OT_HideOrnamentBasewear1(PSO2_OT_HideOrnament):
    bl_label = "Hide Basewear 1"
    bl_idname = "pso2.hide_basewear_ornament_1"
    mesh_id = 3


@classes.register
class PSO2_OT_ShowOrnamentBasewear2(PSO2_OT_ShowOrnament):
    bl_label = "Show Basewear 2"
    bl_idname = "pso2.show_basewear_ornament_2"
    mesh_id = 8


@classes.register
class PSO2_OT_HideOrnamentBasewear2(PSO2_OT_HideOrnament):
    bl_label = "Hide Basewear 2"
    bl_idname = "pso2.hide_basewear_ornament_2"
    mesh_id = 8


@classes.register
class PSO2_OT_ShowOrnamentOuterwear(PSO2_OT_ShowOrnament):
    bl_label = "Show Outerwear"
    bl_idname = "pso2.show_outerwear_ornament"
    mesh_id = 13


@classes.register
class PSO2_OT_HideOrnamentOuterwear(PSO2_OT_HideOrnament):
    bl_label = "Hide Outerwear"
    bl_idname = "pso2.hide_outerwear_ornament"
    mesh_id = 13


@classes.register
class PSO2_OT_ShowOrnamentHair(PSO2_OT_ShowOrnament):
    bl_label = "Show Hair/Head Parts"
    bl_idname = "pso2.show_hair_ornament"
    mesh_id = 9


@classes.register
class PSO2_OT_HideOrnamentHair(PSO2_OT_HideOrnament):
    bl_label = "Hide Hair/Head Parts"
    bl_idname = "pso2.hide_hair_ornament_1"
    mesh_id = 9


@classes.register
class PSO2_OT_ShowOrnamentCastBody(PSO2_OT_ShowOrnament):
    bl_label = "Show Body Parts"
    bl_idname = "pso2.show_cast_body_ornament"
    mesh_id = 10


@classes.register
class PSO2_OT_HideOrnamentCastBody(PSO2_OT_HideOrnament):
    bl_label = "Hide Body Parts"
    bl_idname = "pso2.hide_cast_body_ornament"
    mesh_id = 10


@classes.register
class PSO2_OT_ShowOrnamentCastArm(PSO2_OT_ShowOrnament):
    bl_label = "Show Arm Parts"
    bl_idname = "pso2.show_cast_arm_ornament"
    mesh_id = 11


@classes.register
class PSO2_OT_HideOrnamentCastArm(PSO2_OT_HideOrnament):
    bl_label = "Hide Arm Parts"
    bl_idname = "pso2.hide_cast_arm_ornament"
    mesh_id = 11


@classes.register
class PSO2_OT_ShowOrnamentCastLeg(PSO2_OT_ShowOrnament):
    bl_label = "Show Leg Parts"
    bl_idname = "pso2.show_cast_leg_ornament"
    mesh_id = 12


@classes.register
class PSO2_OT_HideOrnamentCastLeg(PSO2_OT_HideOrnament):
    bl_label = "Hide Leg Parts"
    bl_idname = "pso2.hide_cast_leg_ornament"
    mesh_id = 12
