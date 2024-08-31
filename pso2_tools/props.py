from typing import Iterable, cast

import bpy
from bpy_extras.io_utils import orientation_helper


@orientation_helper(axis_forward="-Z", axis_up="Y")
class CommonImportProps:
    use_manual_orientation: bpy.props.BoolProperty(
        name="Manual Orientation",
        description="Specify orientation and scale, instead of using embedded data in FBX file",
        default=False,
    )

    use_anim: bpy.props.BoolProperty(
        name="Import Animation",
        description="Import FBX animation",
        default=True,
    )
    anim_offset: bpy.props.FloatProperty(
        name="Animation Offset",
        description="Offset to apply to animation during import, in frames",
        default=1.0,
    )

    ignore_leaf_bones: bpy.props.BoolProperty(
        name="Ignore Leaf Bones",
        description="Ignore the last bone at the end of each chain (used to mark the length of the previous bone)",
        default=False,
    )
    force_connect_children: bpy.props.BoolProperty(
        name="Force Connect Children",
        description="Force connection of children bones to their parent, even if their computed head/tail "
        "positions do not match (can be useful with pure-joints-type armatures)",
        default=False,
    )
    automatic_bone_orientation: bpy.props.BoolProperty(
        name="Automatic Bone Orientation",
        description="Try to align the major bone axis with the bone children",
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
        default="Y",
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
        default="X",
    )

    def get_fbx_options(self, ignore: Iterable[str] = None):
        operator = cast(bpy.types.Operator, self)
        ignore = ignore or ()

        # pylint: disable-next=no-member
        keywords = operator.as_keywords(ignore=("filter_glob", "filepath", *ignore))
        keywords["use_image_search"] = False

        return keywords

    def draw_import_props_panel(self, layout: bpy.types.UILayout):
        operator = cast(bpy.types.Operator, self)

        layout.use_property_split = True
        layout.use_property_decorate = False

        import_panel_transform_orientation(layout, operator)
        import_panel_animation(layout, operator)
        import_panel_armature(layout, operator)

    def draw_import_props_column(self, layout: bpy.types.UILayout):
        layout.label(text="Armature", icon="ARMATURE_DATA")

        layout.prop(self, "ignore_leaf_bones")
        layout.prop(self, "force_connect_children")
        layout.prop(self, "automatic_bone_orientation")
        sub = layout.column()
        sub.enabled = not self.automatic_bone_orientation
        sub.prop(self, "primary_bone_axis")
        sub.prop(self, "secondary_bone_axis")


def import_panel_transform_orientation(
    layout: bpy.types.UILayout, operator: bpy.types.Operator
):
    header, body = layout.panel(
        "PSO2_import_transform_manual_orientation", default_closed=False
    )
    header.use_property_split = False
    header.prop(operator, "use_manual_orientation", text="")
    header.label(text="Manual Orientation")
    if body:
        body.enabled = operator.use_manual_orientation
        body.prop(operator, "axis_forward")
        body.prop(operator, "axis_up")


def import_panel_animation(layout: bpy.types.UILayout, operator: bpy.types.Operator):
    header, body = layout.panel("PSO2_import_animation", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "use_anim", text="")
    header.label(text="Animation")
    if body:
        body.enabled = operator.use_anim
        body.prop(operator, "anim_offset")


def import_panel_armature(layout: bpy.types.UILayout, operator: bpy.types.Operator):
    header, body = layout.panel("PSO2_import_armature", default_closed=False)
    header.label(text="Armature")
    if body:
        body.prop(operator, "ignore_leaf_bones")
        body.prop(operator, "force_connect_children")
        body.prop(operator, "automatic_bone_orientation")
        sub = body.column()
        sub.enabled = not operator.automatic_bone_orientation
        sub.prop(operator, "primary_bone_axis")
        sub.prop(operator, "secondary_bone_axis")
