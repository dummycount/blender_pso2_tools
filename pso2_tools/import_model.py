from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory
from typing import Optional, Union

import bpy
from bpy.types import Context, Operator, OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from io_scene_fbx import import_fbx
import zamboni

from . import classes, convert, material, preferences
from .colors import Colors, COLOR_CHANNELS
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

    def draw_texture_props(self, context: Context, layout: bpy.types.UILayout):
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

    def draw_armature_props(self, context: Context, layout: bpy.types.UILayout):
        layout.prop(self, "automatic_bone_orientation")

    def import_directory_textures(self, context: Context, directory: Path):
        if self.use_textures:
            material.load_textures(directory)

    def import_aqp(
        self, context: Context, path: Path, object_info: Optional[ObjectInfo] = None
    ):
        original_mats = set(bpy.data.materials.keys())
        object_info = object_info or ObjectInfo.from_file_name(path)

        with TemporaryDirectory() as tempdir:
            fbxfile = Path(tempdir) / path.with_suffix(".fbx").name
            model_info = convert.aqp_to_fbx_with_info(path, fbxfile)

            import_fbx.load(
                self,
                context,
                filepath=str(fbxfile),
                automatic_bone_orientation=self.automatic_bone_orientation,
            )
            material.delete_empty_images()

            # Make sure to load skin textures before creating any materials that
            # would use them.
            if self.use_textures and material.skin_material_exists(model_info):
                self.load_skin_textures(context)

            new_mats = set(bpy.data.materials.keys())
            material.update_materials(
                context,
                new_mats.difference(original_mats),
                object_info,
                model_info,
            )

    def load_skin_textures(self, context: Context):
        # Import skin textures from the base body ICE archive
        body_ice = self.get_object_info().base_body_ice
        if body_ice is None:
            return

        data_dir = preferences.get_preferences(context).get_pso2_data_path()
        if not data_dir.exists():
            return

        base_body = data_dir / "win32" / body_ice

        with TemporaryDirectory() as name:
            tempdir = Path(name)
            zamboni.unpack_ice(base_body, tempdir)

            # ######1 textures are just for muscles, so no need to import those.
            material.load_textures(tempdir, "pl_rbd_*0_sk_*.dds")

    @staticmethod
    def import_ice(
        operator: Union[Operator, "ImportProperties"],
        context: Context,
        filepath: Path | str,
        object_info: Optional[ObjectInfo] = None,
    ):
        """Load a model from an ICE file"""
        filepath = Path(filepath)

        try:
            with TemporaryDirectory() as name:
                tempdir = Path(name)
                zamboni.unpack_ice(filepath, tempdir)

                operator.import_directory_textures(context, tempdir)
                for aqpfile in tempdir.rglob("*.aqp"):
                    operator.import_aqp(context, aqpfile, object_info=object_info)
        except CalledProcessError as ex:
            operator.report({"ERROR"}, f"Failed to import {filepath}:\n{ex.stderr}")
            return {"CANCELLED"}

        return {"FINISHED"}

    @staticmethod
    def import_aqp_and_textures(
        operator: Union[Operator, "ImportProperties"],
        context: Context,
        filepath: Path | str,
    ):
        """Load a model from an AQP file"""
        filepath = Path(filepath)

        try:
            operator.import_directory_textures(context, filepath.parent)
            operator.import_aqp(context, filepath)
        except CalledProcessError as ex:
            operator.report({"ERROR"}, f"Failed to import {filepath}:\n{ex.stderr}")
            return {"CANCELLED"}

        return {"FINISHED"}


class BaseImport(Operator, ImportProperties, ImportHelper):
    directory: bpy.props.StringProperty()

    files: bpy.props.CollectionProperty(name="File Path", type=OperatorFileListElement)

    def draw(self, context):
        pass

    def execute(self, context: Context) -> set[str]:
        if self.files:
            ret = {"CANCELLED"}
            directory = Path(self.filepath).parent
            for file in self.files:
                path = directory / file.name
                result = self.import_model(context, filepath=path)
                if result == {"FINISHED"}:
                    ret = result
            return ret

        return self.import_model(context, filepath=Path(self.filepath))

    def import_model(self, context: Context, filepath: Path) -> set[str]:
        raise NotImplementedError()


def _get_active_operator(context: Context) -> Operator:
    return context.space_data.active_operator


def _is_import_browser(context: Context):
    operator = _get_active_operator(context)
    return operator.bl_idname.startswith("PSO2_TOOLS_OT_import")


@classes.register_class
class PSO2_PT_import_textures(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Textures"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        return _is_import_browser(context)

    def draw(self, context):
        operator: ImportProperties = _get_active_operator(context)
        operator.draw_texture_props(context, self.layout)


@classes.register_class
class PSO2_PT_import_armature(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Armature"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        operator: Operator = context.space_data.active_operator
        return operator.bl_idname.startswith("PSO2_TOOLS_OT_import")

    def draw(self, context):
        operator: ImportProperties = _get_active_operator(context)
        operator.draw_armature_props(context, self.layout)


@classes.register_class
class ImportAqp(BaseImport):
    """Load a PSO2 AQP model"""

    bl_idname = "pso2_tools.import_aqp"
    bl_label = "Import AQP"
    bl_options = {"UNDO", "PRESET"}

    filename_ext = ".aqp"
    filter_glob: bpy.props.StringProperty(default="*.aqp", options={"HIDDEN"})

    def get_filepath(self):
        return self.filepath

    def import_model(self, context, filepath):
        ImportProperties.import_aqp_and_textures(self, context, filepath)


@classes.register_class
class ImportIce(BaseImport):
    """Load a PSO2 AQP model from an ICE archive"""

    bl_idname = "pso2_tools.import_ice"
    bl_label = "Import ICE"
    bl_options = {"UNDO", "PRESET"}

    filter_glob: bpy.props.StringProperty(default="*", options={"HIDDEN"})

    def get_filepath(self):
        path = Path(self.filepath)

        if not path.is_file():
            return ""

        try:
            ice = zamboni.IceFile.read(path)

            for file in ice.group2_files:
                if file.name.endswith(".aqp"):
                    return file.name

            if ice.group2_files:
                return ice.group2_files[0].name
            if ice.group1_files:
                return ice.group1_files[0].name
        except ValueError:
            pass

        return ""

    def import_model(self, context, filepath):
        ImportProperties.import_ice(self, context, filepath)
