from pathlib import Path
import re
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import bpy
from bpy.types import Context, Operator
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy_extras.io_utils import ExportHelper, axis_conversion
from io_scene_fbx import export_fbx_bin

from . import classes, convert

EXPORT_KWARGS = dict(
    global_scale=1.0,
    apply_unit_scale=True,
    use_space_transform=True,
    bake_space_transform=False,
    add_leaf_bones=False,
    armature_nodetype="NULL",
    embed_textures=False,
    batch_mode="OFF",
    global_matrix=axis_conversion(to_forward="-Z", to_up="Y").to_4x4(),
)


class BaseExport(Operator, ExportHelper):
    update_skeleton: BoolProperty(
        name="Update Skeleton",
        description="Overwrite an existing .aqn file from the exported model",
        default=False,
    )

    use_selection: BoolProperty(
        name="Selected Objects",
        description="Export selected and visible objects only",
        default=False,
    )
    use_visible: BoolProperty(
        name="Visible Objects", description="Export visible objects only", default=False
    )
    use_active_collection: BoolProperty(
        name="Active Collection",
        description="Export only objects from the active collection (and its children)",
        default=False,
    )

    object_types: EnumProperty(
        name="Object Types",
        options={"ENUM_FLAG"},
        items=(
            ("EMPTY", "Empty", ""),
            ("CAMERA", "Camera", ""),
            ("LIGHT", "Lamp", ""),
            ("ARMATURE", "Armature", "WARNING: not supported in dupli/group instances"),
            ("MESH", "Mesh", ""),
            (
                "OTHER",
                "Other",
                "Other geometry types, like curve, metaball, etc. (converted to meshes)",
            ),
        ),
        description="Which kind of object to export",
        default={"EMPTY", "ARMATURE", "MESH", "OTHER"},
    )

    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones) - "
        "WARNING: prevents exporting shape keys",
        default=True,
    )
    mesh_smooth_type: EnumProperty(
        name="Smoothing",
        items=(
            (
                "OFF",
                "Normals Only",
                "Export only normals instead of writing edge or face smoothing data",
            ),
            ("FACE", "Face", "Write face smoothing"),
            ("EDGE", "Edge", "Write edge smoothing"),
        ),
        description="Export smoothing information "
        "(prefer 'Normals Only' option if your target importer understand split normals)",
        default="OFF",
    )
    use_subsurf: BoolProperty(
        name="Export Subdivision Surface",
        description="Export the last Catmull-Rom subdivision modifier as FBX subdivision "
        "(does not apply the modifier even if 'Apply Modifiers' is enabled)",
        default=False,
    )
    use_mesh_edges: BoolProperty(
        name="Loose Edges",
        description="Export loose edges (as two-vertices polygons)",
        default=False,
    )
    use_triangles: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles",
        default=False,
    )
    use_custom_props: BoolProperty(
        name="Custom Properties",
        description="Export custom properties",
        default=False,
    )
    primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        items=(
            ("X", "X Axis", ""),
            ("Y", "Y Axis", ""),
            ("Z", "Z Axis", ""),
            ("-X", "-X Axis", ""),
            ("-Y", "-Y Axis", ""),
            ("-Z", "-Z Axis", ""),
        ),
        default="Y",
    )
    secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        items=(
            ("X", "X Axis", ""),
            ("Y", "Y Axis", ""),
            ("Z", "Z Axis", ""),
            ("-X", "-X Axis", ""),
            ("-Y", "-Y Axis", ""),
            ("-Z", "-Z Axis", ""),
        ),
        default="X",
    )
    use_armature_deform_only: BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=False,
    )
    bake_anim: BoolProperty(
        name="Baked Animation",
        description="Export baked keyframe animation",
        default=True,
    )
    bake_anim_use_all_bones: BoolProperty(
        name="Key All Bones",
        description="Force exporting at least one key of animation for all bones "
        "(needed with some target applications, like UE4)",
        default=True,
    )
    bake_anim_use_nla_strips: BoolProperty(
        name="NLA Strips",
        description="Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
        "instead of global scene animation",
        default=True,
    )
    bake_anim_use_all_actions: BoolProperty(
        name="All Actions",
        description="Export each action as a separated FBX's AnimStack, instead of global scene animation "
        "(note that animated objects will get all actions compatible with them, "
        "others will get no animation at all)",
        default=True,
    )
    bake_anim_force_startend_keying: BoolProperty(
        name="Force Start/End Keying",
        description="Always add a keyframe at start and end of actions for animated channels",
        default=True,
    )
    bake_anim_step: FloatProperty(
        name="Sampling Rate",
        description="How often to evaluate animated values (in frames)",
        min=0.01,
        max=100.0,
        soft_min=0.1,
        soft_max=10.0,
        default=1.0,
    )
    bake_anim_simplify_factor: FloatProperty(
        name="Simplify",
        description="How much to simplify baked values (0.0 to disable, the higher the more simplified)",
        min=0.0,
        max=100.0,  # No simplification to up to 10% of current magnitude tolerance.
        soft_min=0.0,
        soft_max=10.0,
        default=1.0,  # default: min slope: 0.005, max frame step: 10.
    )

    def draw(self, context):
        pass

    def execute(self, context):
        if result := self.check_model(context):
            return result

        keywords = EXPORT_KWARGS | self.as_keywords(
            ignore=(
                "check_existing",
                "filter_glob",
                "filepath",
                "ui_tab",
                "update_skeleton",
            )
        )

        with TemporaryDirectory() as name:
            filepath = Path(self.filepath)
            tempdir = Path(name)
            temp_fbx_file = (tempdir / filepath.name).with_suffix(".fbx")

            export_fbx_bin.save(self, context, filepath=str(temp_fbx_file), **keywords)

            if fbx_file := next(tempdir.rglob("*.fbx"), None):
                return self.save_model_file(context, fbx_file, filepath)

            self.report({"ERROR"}, "FBX export failed. No FBX files found.")
            return {"CANCELLED"}

    def save_model_file(
        self, context: Context, fbx_file: Path, filepath: Path
    ) -> set[str]:
        raise NotImplementedError()

    def check_model(self, context: Context):
        # Aqua model tool doesn't like meshes whose names end in a suffix like .001
        def is_invalid(obj: bpy.types.Object):
            return bool(obj.users and re.search(r"\.\d+$", obj.name))

        invalid_objects = [obj for obj in bpy.data.meshes if is_invalid(obj)]

        if invalid_objects:
            names = "\n".join(obj.name for obj in invalid_objects)
            self.report(
                {"ERROR"},
                f'Cannot export to AQP. Remove suffixes like ".001" from the names of these meshes:\n{names}',
            )
            return {"CANCELLED"}

        return None


def _is_export_browser(context: Context):
    operator: Operator = context.space_data.active_operator
    return operator.bl_idname.startswith("PSO2_TOOLS_OT_export")


@classes.register_class
class PSO2_PT_export_main(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        return _is_export_browser(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        operator: BaseExport = context.space_data.active_operator

        layout.prop(operator, "update_skeleton")


@classes.register_class
class PSO2_PT_export_include(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _is_export_browser(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        operator: BaseExport = context.space_data.active_operator

        sublayout = layout.column(heading="Limit to")
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_visible")
        sublayout.prop(operator, "use_active_collection")

        layout.column().prop(operator, "object_types")
        layout.prop(operator, "use_custom_props")


@classes.register_class
class PSO2_PT_export_geometry(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _is_export_browser(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        operator: BaseExport = context.space_data.active_operator

        layout.prop(operator, "mesh_smooth_type")
        layout.prop(operator, "use_subsurf")
        layout.prop(operator, "use_mesh_modifiers")
        layout.prop(operator, "use_mesh_edges")
        layout.prop(operator, "use_triangles")
        sub = layout.row()
        sub.prop(operator, "use_tspace")


@classes.register_class
class PSO2_PT_export_armature(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Armature"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _is_export_browser(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        operator: BaseExport = context.space_data.active_operator

        layout.prop(operator, "primary_bone_axis")
        layout.prop(operator, "secondary_bone_axis")
        layout.prop(operator, "armature_nodetype")
        layout.prop(operator, "use_armature_deform_only")


@classes.register_class
class PSO2_PT_export_bake_animation(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Bake Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _is_export_browser(context)

    def draw_header(self, context):
        operator: BaseExport = context.space_data.active_operator

        self.layout.prop(operator, "bake_anim", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        operator: BaseExport = context.space_data.active_operator

        layout.enabled = operator.bake_anim
        layout.prop(operator, "bake_anim_use_all_bones")
        layout.prop(operator, "bake_anim_use_nla_strips")
        layout.prop(operator, "bake_anim_use_all_actions")
        layout.prop(operator, "bake_anim_force_startend_keying")
        layout.prop(operator, "bake_anim_step")
        layout.prop(operator, "bake_anim_simplify_factor")


@classes.register_class
class ExportAqp(BaseExport):
    """Save a PSO2 AQP model"""

    bl_idname = "pso2_tools.export_aqp"
    bl_label = "Export AQP"
    bl_options = {"UNDO", "PRESET"}

    filename_ext = ".aqp"
    filter_glob: StringProperty(default="*.aqp", options={"HIDDEN"})

    def save_model_file(self, context: Context, fbx_file: Path, filepath: Path):
        args = ["--update-aqn"] if self.update_skeleton else []

        try:
            result = convert.fbx_to_aqp(fbx_file, filepath, *args)
            print(result.returncode, result.stdout, result.stderr)
            return {"FINISHED"}
        except CalledProcessError as ex:
            self.report({"ERROR"}, f"Failed to convert FBX to AQP:\n{ex.stderr}")
            return {"CANCELLED"}
