from pathlib import Path

import bpy
from bpy_extras.io_utils import ExportHelper, axis_conversion, orientation_helper
from mathutils import Matrix

from . import classes, export_model


@classes.register
@orientation_helper(axis_forward="-Z", axis_up="Y")
class PSO2_OT_ExportAqp(bpy.types.Operator, ExportHelper):
    """Write a PSO2 AQP file"""

    bl_label = "Export AQP"
    bl_idname = "pso2.export_aqp"
    bl_options = {"UNDO", "PRESET"}

    filename_ext = ".aqp"
    filter_glob: bpy.props.StringProperty(default="*.aqp", options={"HIDDEN"})

    game_version: bpy.props.EnumProperty(
        name="Game Version",
        items=[
            ("NGS", "NGS", "Export for PSO2 NGS"),
            ("CLASSIC", "Classic", "Export for PSO2 classic"),
        ],
        default="NGS",
    )
    overwrite_aqn: bpy.props.BoolProperty(
        name="Overwrite .aqn",
        description="If a .aqn file with the same name exists, overwrite it",
        default=False,
    )

    use_selection: bpy.props.BoolProperty(
        name="Selected Objects",
        description="Export selected and visible objects only",
        default=False,
    )
    use_visible: bpy.props.BoolProperty(
        name="Visible Objects", description="Export visible objects only", default=False
    )
    use_active_collection: bpy.props.BoolProperty(
        name="Active Collection",
        description="Export only objects from the active collection (and its children)",
        default=False,
    )
    collection: bpy.props.StringProperty(
        name="Source Collection",
        description="Export only objects from this collection (and its children)",
        default="",
    )
    global_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale all data (Some importers do not support scaled armatures!)",
        min=0.001,
        max=1000.0,
        soft_min=0.01,
        soft_max=1000.0,
        default=1.0,
    )
    apply_unit_scale: bpy.props.BoolProperty(
        name="Apply Unit",
        description="Take into account current Blender units settings (if unset, raw Blender Units values are used as-is)",
        default=True,
    )
    apply_scale_options: bpy.props.EnumProperty(
        items=(
            (
                "FBX_SCALE_NONE",
                "All Local",
                "Apply custom scaling and units scaling to each object transformation, FBX scale remains at 1.0",
            ),
            (
                "FBX_SCALE_UNITS",
                "FBX Units Scale",
                "Apply custom scaling to each object transformation, and units scaling to FBX scale",
            ),
            (
                "FBX_SCALE_CUSTOM",
                "FBX Custom Scale",
                "Apply custom scaling to FBX scale, and units scaling to each object transformation",
            ),
            (
                "FBX_SCALE_ALL",
                "FBX All",
                "Apply custom scaling and units scaling to FBX scale",
            ),
        ),
        name="Apply Scalings",
        description="How to apply custom and units scalings in generated FBX file "
        "(Blender uses FBX scale to detect units on import, "
        "but many other applications do not handle the same way)",
    )

    use_space_transform: bpy.props.BoolProperty(
        name="Use Space Transform",
        description="Apply global space transform to the object rotations. When disabled "
        "only the axis space is written to the file and all object transforms are left as-is",
        default=True,
    )
    bake_space_transform: bpy.props.BoolProperty(
        name="Apply Transform",
        description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
        "target space is not aligned with Blender's space "
        "(WARNING! experimental option, use at own risk, known to be broken with armatures/animations)",
        default=False,
    )

    use_mesh_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones) - "
        "WARNING: prevents exporting shape keys",
        default=True,
    )

    mesh_smooth_type: bpy.props.EnumProperty(
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

    use_subsurf: bpy.props.BoolProperty(
        name="Export Subdivision Surface",
        description="Export the last Catmull-Rom subdivision modifier as FBX subdivision "
        "(does not apply the modifier even if 'Apply Modifiers' is enabled)",
        default=False,
    )
    use_mesh_edges: bpy.props.BoolProperty(
        name="Loose Edges",
        description="Export loose edges (as two-vertices polygons)",
        default=False,
    )
    use_tspace: bpy.props.BoolProperty(
        name="Tangent Space",
        description="Add binormal and tangent vectors, together with normal they form the tangent space "
        "(will only work correctly with tris/quads only meshes!)",
        default=False,
    )
    use_triangles: bpy.props.BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles",
        default=True,
    )
    add_leaf_bones: bpy.props.BoolProperty(
        name="Add Leaf Bones",
        description="Append a final bone to the end of each chain to specify last bone length "
        "(use this when you intend to edit the armature from exported data)",
        default=False,
    )
    primary_bone_axis: bpy.props.EnumProperty(
        name="Primary Bone Axis",
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
    secondary_bone_axis: bpy.props.EnumProperty(
        name="Secondary Bone Axis",
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
    use_armature_deform_only: bpy.props.BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=False,
    )
    armature_nodetype: bpy.props.EnumProperty(
        name="Armature FBXNode Type",
        items=(
            ("NULL", "Null", "'Null' FBX node, similar to Blender's Empty (default)"),
            (
                "ROOT",
                "Root",
                "'Root' FBX node, supposed to be the root of chains of bones...",
            ),
            (
                "LIMBNODE",
                "LimbNode",
                "'LimbNode' FBX node, a regular joint between two bones...",
            ),
        ),
        description="FBX type of node (object) used to represent Blender's armatures "
        "(use the Null type unless you experience issues with the other app, "
        "as other choices may not import back perfectly into Blender...)",
        default="NULL",
    )
    bake_anim: bpy.props.BoolProperty(
        name="Baked Animation",
        description="Export baked keyframe animation",
        default=True,
    )
    bake_anim_use_all_bones: bpy.props.BoolProperty(
        name="Key All Bones",
        description="Force exporting at least one key of animation for all bones "
        "(needed with some target applications, like UE4)",
        default=True,
    )
    bake_anim_use_nla_strips: bpy.props.BoolProperty(
        name="NLA Strips",
        description="Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
        "instead of global scene animation",
        default=True,
    )
    bake_anim_use_all_actions: bpy.props.BoolProperty(
        name="All Actions",
        description="Export each action as a separated FBX's AnimStack, instead of global scene animation "
        "(note that animated objects will get all actions compatible with them, "
        "others will get no animation at all)",
        default=True,
    )
    bake_anim_force_startend_keying: bpy.props.BoolProperty(
        name="Force Start/End Keying",
        description="Always add a keyframe at start and end of actions for animated channels",
        default=True,
    )
    bake_anim_step: bpy.props.FloatProperty(
        name="Sampling Rate",
        description="How often to evaluate animated values (in frames)",
        min=0.01,
        max=100.0,
        soft_min=0.1,
        soft_max=10.0,
        default=1.0,
    )
    bake_anim_simplify_factor: bpy.props.FloatProperty(
        name="Simplify",
        description="How much to simplify baked values (0.0 to disable, the higher the more simplified)",
        min=0.0,
        max=100.0,  # No simplification to up to 10% of current magnitude tolerance.
        soft_min=0.0,
        soft_max=10.0,
        default=1.0,  # default: min slope: 0.005, max frame step: 10.
    )
    batch_mode: bpy.props.StringProperty(
        name="Batch Mode",
        default="OFF",
        options={"HIDDEN"},
    )
    use_metadata: bpy.props.BoolProperty(
        name="Use Metadata",
        default=True,
        options={"HIDDEN"},
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        is_file_browser = context.space_data.type == "FILE_BROWSER"

        export_panel_main(layout, self)
        export_panel_include(layout, self, is_file_browser)
        export_panel_transform(layout, self)
        export_panel_geometry(layout, self)
        export_panel_armature(layout, self)
        export_panel_animation(layout, self)

    def execute(self, context):  # type: ignore
        if not self.filepath:  # pylint: disable=no-member # type: ignore
            raise ValueError("filepath not set")

        path = Path(self.filepath)  # pylint: disable=no-member # type: ignore

        global_matrix = (
            # pylint: disable-next=no-member
            axis_conversion(to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()  # type: ignore
            if self.use_space_transform
            else Matrix()
        )

        options = self.as_keywords(
            ignore=(
                "check_existing",
                "filter_glob",
                "filepath",
                "version",
                "overwrite_aqn",
            )
        )
        # pylint: disable-next=unsupported-assignment-operation
        options["global_matrix"] = global_matrix

        return export_model.export(
            self,
            context,
            path,
            is_ngs=self.game_version == "NGS",
            overwrite_aqn=self.overwrite_aqn,
            fbx_options=options,
        )


def export_panel_main(layout: bpy.types.UILayout, operator):
    layout.prop(operator, "overwrite_aqn")
    layout.prop(operator, "game_version")


def export_panel_include(layout: bpy.types.UILayout, operator, is_file_browser: bool):
    if not is_file_browser:
        return

    header, body = layout.panel("PSO2_export_include", default_closed=False)
    header.label(text="Include")
    if body:
        sublayout = body.column(heading="Limit to")
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_visible")
        sublayout.prop(operator, "use_active_collection")


def export_panel_transform(layout: bpy.types.UILayout, operator):
    header, body = layout.panel("PSO2_export_transform", default_closed=True)
    header.label(text="Transform")
    if body:
        body.prop(operator, "global_scale")
        body.prop(operator, "apply_scale_options")

        body.prop(operator, "axis_forward")
        body.prop(operator, "axis_up")

        body.prop(operator, "apply_unit_scale")
        body.prop(operator, "use_space_transform")
        row = body.row()
        row.prop(operator, "bake_space_transform")
        row.label(text="", icon="ERROR")


def export_panel_geometry(layout: bpy.types.UILayout, operator):
    header, body = layout.panel("PSO2_export_geometry", default_closed=False)
    header.label(text="Geometry")
    if body:
        body.prop(operator, "mesh_smooth_type")
        body.prop(operator, "use_subsurf")
        body.prop(operator, "use_mesh_modifiers")
        body.prop(operator, "use_mesh_edges")
        body.prop(operator, "use_triangles")
        sub = body.row()
        # ~ sub.enabled = operator.mesh_smooth_type in {'OFF'}
        sub.prop(operator, "use_tspace")


def export_panel_armature(layout: bpy.types.UILayout, operator):
    header, body = layout.panel("PSO2_export_armature", default_closed=True)
    header.label(text="Armature")
    if body:
        body.prop(operator, "primary_bone_axis")
        body.prop(operator, "secondary_bone_axis")
        body.prop(operator, "armature_nodetype")
        body.prop(operator, "use_armature_deform_only")
        body.prop(operator, "add_leaf_bones")


def export_panel_animation(layout: bpy.types.UILayout, operator):
    header, body = layout.panel("PSO2_export_bake_animation", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "bake_anim", text="")
    header.label(text="Animation")
    if body:
        body.enabled = operator.bake_anim
        body.prop(operator, "bake_anim_use_all_bones")
        body.prop(operator, "bake_anim_use_nla_strips")
        body.prop(operator, "bake_anim_use_all_actions")
        body.prop(operator, "bake_anim_force_startend_keying")
        body.prop(operator, "bake_anim_step")
        body.prop(operator, "bake_anim_simplify_factor")
