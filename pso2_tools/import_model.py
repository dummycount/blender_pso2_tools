from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

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


from . import classes, convert, material, preferences
from .shaders import default_colors


BASE_BODY_ICE = {
    "T1": "195fac68420e7a08fb37ae36403a419b",
    "T2": "be23da464641f6ea102f4366095fa5eb",
}


def convert_textures(source: Path, dest: Path):
    for dds in source.glob("*.dds"):
        png = dest / dds.with_suffix(".png").relative_to(source)
        convert.dds_to_png(dds, png)


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
    body_type: EnumProperty(
        name="Body Type",
        items=(
            ("NONE", "None", "Do not import skin textures"),
            ("T1", "T1", "Use T1 skin textures"),
            ("T2", "T2", "Use T2 skin textures"),
        ),
        description="Body type for skin textures",
        default="T2",
    )
    custom_color_1: FloatVectorProperty(
        name="Outfit 1",
        description="Custom outfit color 1",
        default=default_colors.BASE_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_2: FloatVectorProperty(
        name="Outfit 2",
        description="Custom outfit color 2",
        default=default_colors.BASE_COLOR_2,
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

    def draw_texture_props(self, context: Context, layout: bpy.types.UILayout):
        layout.use_property_split = True

        layout.prop(self, "use_textures")
        layout.prop(self, "body_type")
        layout.prop(self, "main_skin_color")
        layout.prop(self, "sub_skin_color")
        layout.prop(self, "custom_color_1")
        layout.prop(self, "custom_color_2")
        layout.prop(self, "inner_color_1")
        layout.prop(self, "inner_color_2")
        layout.prop(self, "hair_color_1")
        layout.prop(self, "hair_color_2")
        layout.prop(self, "eye_color")

    def draw_armature_props(self, context: Context, layout: bpy.types.UILayout):
        layout.prop(self, "automatic_bone_orientation")

    def load_files_from_directory(self, context: Context, directory: Path) -> set[str]:
        from io_scene_fbx import import_fbx

        colors = material.CustomColors(
            custom_color_1=self.custom_color_1,
            custom_color_2=self.custom_color_2,
            main_skin_color=self.main_skin_color,
            sub_skin_color=self.sub_skin_color,
            inner_color_1=self.inner_color_1,
            inner_color_2=self.inner_color_2,
            hair_color_1=self.hair_color_1,
            hair_color_2=self.hair_color_2,
            eye_color=self.eye_color,
        )

        if self.use_textures:
            material.load_textures(directory)

        if files := list(directory.rglob("*.fbx")):
            original_mats = set(bpy.data.materials.keys())

            for fbxfile in files:
                import_fbx.load(
                    self,
                    context,
                    filepath=str(fbxfile),
                    automatic_bone_orientation=self.automatic_bone_orientation,
                )
                material.delete_empty_images()

            # Make to to load skin textures before creating any materials that
            # would use them.
            if self.use_textures and material.skin_material_exists():
                self.load_skin_textures(context)

            new_mats = set(bpy.data.materials.keys())
            material.update_materials(new_mats.difference(original_mats), colors)

        return {"FINISHED"}

    def load_skin_textures(self, context: Context):
        # Import skin textures from the base body ICE archive
        body_ice = BASE_BODY_ICE.get(self.body_type, None)
        if body_ice is None:
            return

        data_dir = Path(preferences.get_preferences(context).pso2_data_path)
        if not data_dir.exists():
            return

        base_body = data_dir / "win32" / body_ice

        with TemporaryDirectory() as name:
            tempdir = Path(name)
            convert.unpack_ice(base_body, tempdir, "--png")

            # ######1 textures are just for muscles, so no need to import those.
            material.load_textures(tempdir, "pl_rbd_*0_sk_*.png")

    @staticmethod
    def load_ice_model(operator: Operator, context: Context, filepath: Path | str):
        try:
            with TemporaryDirectory() as name:
                tempdir = Path(name)
                convert.unpack_ice(filepath, tempdir, "--fbx", "--png")

                return operator.load_files_from_directory(context, tempdir)
        except CalledProcessError as ex:
            operator.report({"ERROR"}, f"Failed to import {filepath}:\n{ex.stderr}")
            return {"CANCELLED"}

    @staticmethod
    def load_aqp_model(operator: Operator, context: Context, filepath: Path | str):
        try:
            with TemporaryDirectory() as name:
                tempdir = Path(name)
                convert.aqp_to_fbx(
                    filepath, tempdir / filepath.with_suffix(".fbx").name
                )

                if operator.use_textures:
                    convert_textures(filepath.parent, tempdir)

                return operator.load_files_from_directory(context, tempdir)
        except CalledProcessError as ex:
            operator.report({"ERROR"}, f"Failed to import {filepath}:\n{ex.stderr}")
            return {"CANCELLED"}


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
                result = self.load_model_file(context, filepath=path)
                if result == {"FINISHED"}:
                    ret = result
            return ret

        return self.load_model_file(context, filepath=Path(self.filepath))

    def load_model_file(self, context: Context, filepath: Path) -> set[str]:
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

    def load_model_file(self, context, filepath):
        ImportProperties.load_aqp_model(self, context, filepath)


@classes.register_class
class ImportIce(BaseImport):
    """Load a PSO2 AQP model from an ICE archive"""

    bl_idname = "pso2_tools.import_ice"
    bl_label = "Import ICE"
    bl_options = {"UNDO", "PRESET"}

    filter_glob: StringProperty(default="*", options={"HIDDEN"})

    def load_model_file(self, context, filepath):
        ImportProperties.load_ice_model(self, context, filepath)
