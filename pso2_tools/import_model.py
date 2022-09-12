from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

if "bpy" in locals():
    import importlib

    if "bin" in locals():
        importlib.reload(bin)
    if "material" in locals():
        importlib.reload(material)


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

from . import bin, material
from .classes import register_class
from .preferences import get_preferences


BASE_BODY_ICE = {
    "T1": "195fac68420e7a08fb37ae36403a419b",
    "T2": "be23da464641f6ea102f4366095fa5eb",
}


class BaseImport(Operator, ImportHelper):
    directory: StringProperty()

    files: CollectionProperty(name="File Path", type=OperatorFileListElement)

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
    custom_color1: FloatVectorProperty(
        name="Color 1",
        description="Custom outfit color 1",
        default=(0.5, 0.5, 0.5, 1.0),
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color2: FloatVectorProperty(
        name="Color 2",
        description="Custom outfit color 2",
        default=(0.5, 0.5, 0.5, 1.0),
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
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
    skin_color: FloatVectorProperty(
        name="Skin Color",
        description="Skin color",
        default=(1.0, 0.45, 0.33, 1.0),
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )

    def draw(self, context):
        pass

    def execute(self, context):
        if self.use_textures:
            self.load_body_textures(context)

        return self.load_models(context)

    def load_models(self, context: Context) -> set[str]:
        if self.files:
            ret = {"CANCELLED"}
            directory = Path(self.filepath).parent
            for file in self.files:
                path = directory / file.name
                result = self.load_model_file(context, filepath=path)
                if result == {"FINISHED"}:
                    ret = result
            return ret
        else:
            return self.load_model_file(context, filepath=Path(self.filepath))

    def load_model_file(self, context: Context, filepath: Path) -> set[str]:
        raise NotImplementedError()

    def load_fbx_from_directory(self, context: Context, directory: Path) -> set[str]:
        from io_scene_fbx import import_fbx

        colors = material.CustomColors(
            custom_color1=self.custom_color1,
            custom_color2=self.custom_color2,
            skin_color=self.skin_color,
        )

        if files := list(directory.rglob("*.fbx")):
            original_mats = set(bpy.data.materials.keys())

            for fbxfile in files:
                import_fbx.load(
                    self,
                    context,
                    filepath=str(fbxfile),
                    automatic_bone_orientation=self.automatic_bone_orientation,
                )

            new_mats = set(bpy.data.materials.keys())

            if self.use_textures:
                material.load_textures(directory)

            material.update_materials(new_mats.difference(original_mats), colors)
            return {"FINISHED"}

        self.report({"ERROR"}, "No model files found")
        return {"CANCELLED"}

    def load_body_textures(self, context: Context):
        # Import skin textures from the base body ICE archive
        body_ice = BASE_BODY_ICE.get(self.body_type, None)
        if body_ice is None:
            return

        data_dir = Path(get_preferences(context).pso2_data_path)
        if not data_dir.exists():
            return

        base_body = data_dir / "win32" / body_ice

        with TemporaryDirectory() as name:
            tempdir = Path(name)
            bin.unpack_ice(base_body, tempdir, "--png")

            # ######1 textures are just for muscles, so no need to import those.
            material.load_textures(tempdir, "pl_rbd_*0_sk_*.png")


def _is_import_browser(context: Context):
    operator: Operator = context.space_data.active_operator
    return operator.bl_idname.startswith("PSO2_TOOLS_OT_import")


@register_class
class PSO2_PT_import_textures(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Import Textures"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        return _is_import_browser(context)

    def draw_header(self, context):
        operator: BaseImport = context.space_data.active_operator

        self.layout.prop(operator, "use_textures", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        operator: BaseImport = context.space_data.active_operator

        layout.enabled = operator.use_textures
        layout.prop(operator, "custom_color1")
        layout.prop(operator, "custom_color2")
        layout.prop(operator, "body_type")
        layout.prop(operator, "skin_color")


@register_class
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
        layout = self.layout
        operator: BaseImport = context.space_data.active_operator

        layout.prop(operator, "automatic_bone_orientation")


@register_class
class ImportAqp(BaseImport):
    """Load a PSO2 AQP model"""

    bl_idname = "pso2_tools.import_aqp"
    bl_label = "Import AQP"
    bl_options = {"UNDO", "PRESET"}

    filename_ext = ".aqp"
    filter_glob: StringProperty(default="*.aqp", options={"HIDDEN"})

    def load_model_file(self, context, filepath):
        try:
            with TemporaryDirectory() as name:
                tempdir = Path(name)
                bin.aqp_to_fbx(filepath, tempdir / filepath.with_suffix(".fbx").name)

                if self.use_textures:
                    self.convert_textures(filepath.parent, tempdir)

                return self.load_fbx_from_directory(context, tempdir)
        except CalledProcessError as ex:
            self.report({"ERROR"}, f"Failed to convert {filepath} to FBX:\n{ex.stderr}")
            return {"CANCELLED"}

    def convert_textures(self, source: Path, dest: Path):
        for dds in source.glob("*.dds"):
            png = dest / dds.with_suffix(".png").relative_to(source)
            bin.dds_to_png(dds, png)


@register_class
class ImportIce(BaseImport):
    """Load a PSO2 AQP model from an ICE archive"""

    bl_idname = "pso2_tools.import_ice"
    bl_label = "Import ICE"
    bl_options = {"UNDO", "PRESET"}

    filter_glob: StringProperty(default="*", options={"HIDDEN"})

    def load_model_file(self, context, filepath):
        try:
            with TemporaryDirectory() as name:
                tempdir = Path(name)
                bin.unpack_ice(filepath, tempdir, "--fbx", "--png")

                return self.load_fbx_from_directory(context, tempdir)
        except CalledProcessError as ex:
            self.report(
                {"ERROR"}, f"Failed to convert {filepath} to FBX:\n{ex.stderrr}"
            )
            return {"CANCELLED"}
