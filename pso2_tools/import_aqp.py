from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from . import classes, import_model, props


@classes.register
class PSO2_OT_ImportAqp(bpy.types.Operator, props.CommonImportProps, ImportHelper):
    """Load a PSO2 AQP file"""

    bl_label = "Import AQP"
    bl_idname = "pso2.import_aqp"
    bl_options = {"UNDO", "PRESET"}

    filter_glob: bpy.props.StringProperty(default="*.aqp", options={"HIDDEN"})

    def draw(self, context):
        self.draw_import_props_panel(self.layout)

    def execute(self, context):
        path = Path(self.filepath)  # pylint: disable=no-member

        import_model.import_aqp_file(
            self, context, path, fbx_options=self.get_fbx_options()
        )

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.invoke_popup(context)
