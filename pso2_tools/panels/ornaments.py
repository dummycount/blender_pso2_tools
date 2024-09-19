import re
from typing import Type

import bpy

from .. import classes, util

ORNAMENT_MESHES = ["3", "8", "9", "10", "11", "12", "13"]


@classes.register
class PSO2OrnamentsPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_pso2_ornaments"
    bl_label = "PSO2 Ornaments"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return any(
            m.group(1) in ORNAMENT_MESHES
            for obj in bpy.data.objects
            if obj.type == "MESH"
            and (m := MESH_ID_RE.search(util.remove_blender_suffix(obj.name)))
        )

    def draw(self, context):
        layout = self.layout

        draw_toggle(
            layout,
            "Basewear 1",
            PSO2_OT_ShowOrnamentBasewear1,
            PSO2_OT_HideOrnamentBasewear1,
        )
        draw_toggle(
            layout,
            "Basewear 2",
            PSO2_OT_ShowOrnamentBasewear2,
            PSO2_OT_HideOrnamentBasewear2,
        )
        draw_toggle(
            layout,
            "Outerwear",
            PSO2_OT_ShowOrnamentOuterwear,
            PSO2_OT_HideOrnamentOuterwear,
        )

        layout.separator()

        draw_toggle(
            layout,
            "Hair/Head Parts",
            PSO2_OT_ShowOrnamentHair,
            PSO2_OT_HideOrnamentHair,
        )

        draw_toggle(
            layout,
            "Body Parts",
            PSO2_OT_ShowOrnamentCastBody,
            PSO2_OT_HideOrnamentCastBody,
        )

        draw_toggle(
            layout,
            "Arm Parts",
            PSO2_OT_ShowOrnamentCastArm,
            PSO2_OT_HideOrnamentCastArm,
        )

        draw_toggle(
            layout,
            "Leg Parts",
            PSO2_OT_ShowOrnamentCastLeg,
            PSO2_OT_HideOrnamentCastLeg,
        )


def draw_toggle(
    layout: bpy.types.UILayout,
    label: str,
    show: Type["PSO2_OT_ShowOrnament"],
    hide: Type["PSO2_OT_HideOrnament"],
):
    if not show.is_enabled():
        return

    row = layout.row(align=True)
    row.label(text=label)
    row.operator(show.bl_idname, depress=show.is_depressed())
    row.operator(hide.bl_idname, depress=hide.is_depressed())


MESH_ID_RE = re.compile(r"#(\d+)$")


def has_ornament_mesh(mesh_id: str):
    return any(
        m.group(1) == mesh_id
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and (m := MESH_ID_RE.search(util.remove_blender_suffix(obj.name)))
    )


def get_ornament_mesh_objects(mesh_id: str):
    return [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and (m := MESH_ID_RE.search(util.remove_blender_suffix(obj.name)))
        and m.group(1) == mesh_id
    ]


def find_context_area():
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            return area

    return None


class PSO2_OT_ShowOrnament(bpy.types.Operator):
    bl_label = "Show"
    bl_options = {"UNDO", "REGISTER", "INTERNAL"}
    mesh_id = "0"

    def execute(self, context):  # type: ignore
        for mesh in get_ornament_mesh_objects(self.mesh_id):
            mesh.hide_set(False)

        return {"FINISHED"}

    @classmethod
    def is_enabled(cls) -> bool:
        return has_ornament_mesh(cls.mesh_id)

    @classmethod
    def is_depressed(cls) -> bool:
        meshes = get_ornament_mesh_objects(cls.mesh_id)
        return bool(meshes) and all(not mesh.hide_get() for mesh in meshes)


class PSO2_OT_HideOrnament(bpy.types.Operator):
    bl_label = "Hide"
    bl_options = {"UNDO", "REGISTER", "INTERNAL"}
    mesh_id = "0"

    def execute(self, context):  # type: ignore
        for mesh in get_ornament_mesh_objects(self.mesh_id):
            mesh.hide_set(True)

        return {"FINISHED"}

    @classmethod
    def is_depressed(cls) -> bool:
        meshes = get_ornament_mesh_objects(cls.mesh_id)
        return bool(meshes) and all(mesh.hide_get() for mesh in meshes)


@classes.register
class PSO2_OT_ShowOrnamentBasewear1(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_basewear_ornament_1"
    mesh_id = "3"


@classes.register
class PSO2_OT_HideOrnamentBasewear1(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_basewear_ornament_1"
    mesh_id = "3"


@classes.register
class PSO2_OT_ShowOrnamentBasewear2(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_basewear_ornament_2"
    mesh_id = "8"


@classes.register
class PSO2_OT_HideOrnamentBasewear2(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_basewear_ornament_2"
    mesh_id = "8"


@classes.register
class PSO2_OT_ShowOrnamentOuterwear(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_outerwear_ornament"
    mesh_id = "13"


@classes.register
class PSO2_OT_HideOrnamentOuterwear(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_outerwear_ornament"
    mesh_id = "13"


@classes.register
class PSO2_OT_ShowOrnamentHair(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_hair_ornament"
    mesh_id = "9"


@classes.register
class PSO2_OT_HideOrnamentHair(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_hair_ornament_1"
    mesh_id = "9"


@classes.register
class PSO2_OT_ShowOrnamentCastBody(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_cast_body_ornament"
    mesh_id = "10"


@classes.register
class PSO2_OT_HideOrnamentCastBody(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_cast_body_ornament"
    mesh_id = "10"


@classes.register
class PSO2_OT_ShowOrnamentCastArm(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_cast_arm_ornament"
    mesh_id = "11"


@classes.register
class PSO2_OT_HideOrnamentCastArm(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_cast_arm_ornament"
    mesh_id = "11"


@classes.register
class PSO2_OT_ShowOrnamentCastLeg(PSO2_OT_ShowOrnament):
    bl_idname = "pso2.show_cast_leg_ornament"
    mesh_id = "12"


@classes.register
class PSO2_OT_HideOrnamentCastLeg(PSO2_OT_HideOrnament):
    bl_idname = "pso2.hide_cast_leg_ornament"
    mesh_id = "12"
