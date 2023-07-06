from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory
from typing import Union

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatVectorProperty,
    StringProperty,
)
from bpy.types import Context, Operator, OperatorFileListElement
from bpy_extras.io_utils import ImportHelper

from .object_info import ObjectInfo
import zamboni

from . import classes, convert, material, preferences
from .shaders import default_colors


BASE_BODY_ICE = {
    "T1": "195fac68420e7a08fb37ae36403a419b",
    "T2": "be23da464641f6ea102f4366095fa5eb",
}


class ImportProperties:
    """Mixin class for model import properties"""

    automatic_bone_orientation: BoolProperty(
        name="Automatic Bone Orientation",
        description="Correct bone orientation for Blender (breaks exporting the skeleton back to PSO2)",
        default=False,
    )
    use_textures: BoolProperty(
        name="Import textures",
        description="Import DDS textures from the model directory",
        default=True,
    )
    custom_color_1: FloatVectorProperty(
        name="Color 1",
        description="Custom outfit/cast part color 1",
        default=default_colors.BASE_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_2: FloatVectorProperty(
        name="Color 2",
        description="Custom outfit/cast part color 2",
        default=default_colors.BASE_COLOR_2,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_3: FloatVectorProperty(
        name="Color 3",
        description="Custom cast part color 3",
        default=default_colors.BASE_COLOR_3,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_4: FloatVectorProperty(
        name="Color 4",
        description="Custom outfit color 4",
        default=default_colors.BASE_COLOR_4,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    inner_color_1: FloatVectorProperty(
        name="Innerwear 1",
        description="Custom innerwear color 1",
        default=default_colors.INNER_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    inner_color_2: FloatVectorProperty(
        name="Innerwear 2",
        description="Custom innerwear color 2",
        default=default_colors.INNER_COLOR_2,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    hair_color_1: FloatVectorProperty(
        name="Hair 1",
        description="Hair color 1",
        default=default_colors.HAIR_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    hair_color_2: FloatVectorProperty(
        name="Hair 2",
        description="Hair color 2",
        default=default_colors.HAIR_COLOR_2,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    eye_color: FloatVectorProperty(
        name="Eye",
        description="Eye color",
        default=default_colors.EYE_COLOR,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    main_skin_color: FloatVectorProperty(
        name="Skin Main",
        description="Main skin color",
        default=default_colors.MAIN_SKIN_COLOR,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    sub_skin_color: FloatVectorProperty(
        name="Skin Sub",
        description="Secondary skin color",
        default=default_colors.SUB_SKIN_COLOR,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )

    def get_filepath(self):
        raise NotImplementedError()

    def get_object_info(self):
        name = Path(self.get_filepath()).name
        return ObjectInfo.from_file_name(name)

    def draw_texture_props(self, context: Context, layout: bpy.types.UILayout):
        object_info = self.get_object_info()

        layout.use_property_split = True

        layout.prop(self, "use_textures")
        if object_info.use_skin_colors:
            layout.prop(self, "main_skin_color")
            layout.prop(self, "sub_skin_color")

        if object_info.use_costume_colors or object_info.use_cast_colors:
            layout.prop(self, "custom_color_1")
            layout.prop(self, "custom_color_2")
            if object_info.use_cast_colors:
                layout.prop(self, "custom_color_3")
                layout.prop(self, "custom_color_4")

        if object_info.use_costume_colors:
            layout.prop(self, "inner_color_1")
            layout.prop(self, "inner_color_2")

        if object_info.use_hair_colors:
            layout.prop(self, "hair_color_1")
            layout.prop(self, "hair_color_2")

        if object_info.use_eye_colors:
            layout.prop(self, "eye_color")

    def draw_armature_props(self, context: Context, layout: bpy.types.UILayout):
        layout.prop(self, "automatic_bone_orientation")

    def import_directory_textures(self, context: Context, directory: Path):
        if self.use_textures:
            material.load_textures(directory)

    def import_aqp(self, context: Context, path: Path):
        from io_scene_fbx import import_fbx

        colors = material.CustomColors(
            custom_color_1=self.custom_color_1,
            custom_color_2=self.custom_color_2,
            custom_color_3=self.custom_color_3,
            custom_color_4=self.custom_color_4,
            main_skin_color=self.main_skin_color,
            sub_skin_color=self.sub_skin_color,
            inner_color_1=self.inner_color_1,
            inner_color_2=self.inner_color_2,
            hair_color_1=self.hair_color_1,
            hair_color_2=self.hair_color_2,
            eye_color=self.eye_color,
        )

        original_mats = set(bpy.data.materials.keys())
        object_info = ObjectInfo.from_file_name(path)

        with TemporaryDirectory() as tempdir:
            fbxfile = Path(tempdir) / path.with_suffix(".fbx").name
            convert.aqp_to_fbx(path, fbxfile)

            import_fbx.load(
                self,
                context,
                filepath=str(fbxfile),
                automatic_bone_orientation=self.automatic_bone_orientation,
            )
            material.delete_empty_images()

            # Make sure to load skin textures before creating any materials that
            # would use them.
            if self.use_textures and material.skin_material_exists():
                self.load_skin_textures(context)

            new_mats = set(bpy.data.materials.keys())
            material.update_materials(
                new_mats.difference(original_mats), colors, object_info
            )

    def load_skin_textures(self, context: Context):
        # Import skin textures from the base body ICE archive
        body_ice = self.get_object_info().base_body_ice
        if body_ice is None:
            return

        data_dir = Path(preferences.get_preferences(context).pso2_data_path)
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
    ):
        """Load a model from an ICE file"""
        filepath = Path(filepath)

        try:
            with TemporaryDirectory() as name:
                tempdir = Path(name)
                zamboni.unpack_ice(filepath, tempdir)

                operator.import_directory_textures(context, tempdir)
                for aqpfile in tempdir.rglob("*.aqp"):
                    operator.import_aqp(context, aqpfile)
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
    directory: StringProperty()

    files: CollectionProperty(name="File Path", type=OperatorFileListElement)

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
    filter_glob: StringProperty(default="*.aqp", options={"HIDDEN"})

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

    filter_glob: StringProperty(default="*", options={"HIDDEN"})

    def get_filepath(self):
        path = Path(self.filepath)

        if not path.is_file():
            return ""

        try:
            ice = zamboni.IceFile.read(path)
            print(file.name for file in ice.group2_files)

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
