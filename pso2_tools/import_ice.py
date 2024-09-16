from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from . import classes, import_model, import_props


@classes.register
class PSO2_OT_ImportIce(
    bpy.types.Operator, import_props.CommonImportProps, ImportHelper
):
    """Load a PSO2 ICE archive"""

    bl_label = "Import ICE"
    bl_idname = "pso2.import_ice"
    bl_options = {"UNDO", "PRESET"}

    filter_glob: bpy.props.StringProperty(default="*", options={"HIDDEN"})

    def draw(self, context):
        self.draw_import_props_panel(self.layout)

    def execute(self, context):  # type: ignore
        path = Path(self.filepath)  # pylint: disable=no-member # type: ignore

        import_model.import_ice_file(
            self, context, path, fbx_options=self.get_fbx_options()
        )

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.invoke_popup(context)
