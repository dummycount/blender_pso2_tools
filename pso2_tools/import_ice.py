from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from . import classes, import_model


@classes.register
class PSO2_OT_ImportIce(bpy.types.Operator, ImportHelper):
    bl_label = "Import ICE"
    bl_idname = "pso2.import_ice"
    bl_options = {"UNDO", "PRESET"}

    filter_glob: bpy.props.StringProperty(default="*", options={"HIDDEN"})

    # TODO: add common import properties, e.g. automatic bone orientation

    def execute(self, context):
        path = Path(self.filepath)  # pylint: disable=no-member

        import_model.import_ice_file(self, context, path)

        return {"FINISHED"}
