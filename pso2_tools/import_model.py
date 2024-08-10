from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import bpy

from . import preferences
from .colors import COLOR_CHANNELS, Colors
from .object_info import ObjectInfo


class ImportProperties:
    """Mixin class for model import properties"""

    automatic_bone_orientation: bpy.props.BoolProperty(
        name="Automatic Bone Orientation",
        description="Correct bone orientation for Blender (breaks exporting the skeleton back to PSO2)",
        default=False,
    )
    use_textures: bpy.props.BoolProperty(
        name="Import textures",
        description="Import DDS textures from the model directory",
        default=True,
    )
    use_inner_colors: bpy.props.BoolProperty(
        name="Import textures",
        description="Import DDS textures from the model directory",
        default=True,
    )

    def get_filepath(self):
        raise NotImplementedError()

    def get_object_info(self):
        name = Path(self.get_filepath()).name
        return ObjectInfo.from_file_name(name)

    def draw_texture_props(
        self, context: bpy.types.Context, layout: bpy.types.UILayout
    ):
        prefs = preferences.get_preferences(context)
        object_info = self.get_object_info()

        layout.use_property_split = True

        layout.prop(self, "use_textures")
        if object_info.use_skin_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.MainSkin].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.SubSkin].prop)

        # TODO: filter this better using CMX data
        if object_info.use_cast_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.Cast1].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Cast2].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Cast3].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Cast4].prop)

        # TODO: filter this better using CMX data
        if object_info.use_costume_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.Base1].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Base2].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Outer1].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Outer2].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Inner1].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Inner2].prop)

        if object_info.use_hair_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.Hair1].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.Hair2].prop)

        if object_info.use_eye_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.RightEye].prop)
            layout.prop(prefs, COLOR_CHANNELS[Colors.LeftEye].prop)

        if object_info.use_eyebrow_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.Eyebrow].prop)

        if object_info.use_eyelash_colors:
            layout.prop(prefs, COLOR_CHANNELS[Colors.Eyelash].prop)

    def draw_armature_props(
        self, context: bpy.types.Context, layout: bpy.types.UILayout
    ):
        layout.prop(self, "automatic_bone_orientation")

    def import_directory_textures(self, context: bpy.types.Context, directory: Path):
        if self.use_textures:
            pass
            # material.load_textures(directory)

    def import_aqp(
        self,
        context: bpy.types.Context,
        path: Path,
        object_info: Optional[ObjectInfo] = None,
    ):
        original_mats = set(bpy.data.materials.keys())
        object_info = object_info or ObjectInfo.from_file_name(path)

        with TemporaryDirectory() as tempdir:
            fbxfile = Path(tempdir) / path.with_suffix(".fbx").name
            # model_info = convert.aqp_to_fbx_with_info(path, fbxfile)

            # import_fbx.load(
            #     self,
            #     context,
            #     filepath=str(fbxfile),
            #     automatic_bone_orientation=self.automatic_bone_orientation,
            # )
            # material.delete_empty_images()

            # # Make sure to load skin textures before creating any materials that
            # # would use them.
            # if self.use_textures and material.skin_material_exists(model_info):
            #     self.load_skin_textures(context)

            # new_mats = set(bpy.data.materials.keys())
            # material.update_materials(
            #     context,
            #     new_mats.difference(original_mats),
            #     object_info,
            #     model_info,
            # )
