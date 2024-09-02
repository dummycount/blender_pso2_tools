"""
PSO2 Tools Blender addon
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
import sys

from .paths import ADDON_PATH, BIN_PATH

bl_info = {
    "name": "PSO2 Tools",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "category": "Import-Export",
}

if "reloader" in locals():
    import importlib

    # pylint: disable=used-before-assignment
    importlib.reload(reloader)
    reloader.reload_addon(__name__)

    first_load = False
else:
    first_load = True

import bpy
from pythonnet import load

load("coreclr")

import clr

# Blender complains about this, but there's no other way to get pythonnet
# to find the assemblies.
if str(BIN_PATH) not in sys.path:
    sys.path.append(str(BIN_PATH))

# pylint: disable=no-member
clr.AddReference("System")
clr.AddReference("System.IO")
clr.AddReference("AquaModelLibrary.Core")
clr.AddReference("AquaModelLibrary.Data")
clr.AddReference("AquaModelLibrary.Helpers")
clr.AddReference("ZamboniLib")
# pylint: enable=no-member


from . import classes, export_aqp, import_aqp, import_ice, import_search, reloader
from .panels import appearance, ornaments


def register():
    classes.bpy_register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    classes.bpy_unregister()


def menu_func_import(self: bpy.types.Operator, context: bpy.types.Context):
    self.layout.operator(import_aqp.PSO2_OT_ImportAqp.bl_idname, text="PSO2 AQP (.aqp)")
    self.layout.operator(
        import_ice.PSO2_OT_ImportIce.bl_idname, text="PSO2 ICE Archive"
    )
    self.layout.operator(
        import_search.PSO2_OT_ModelSearch.bl_idname, text="PSO2 Model Search"
    )


def menu_func_export(self: bpy.types.Operator, context: bpy.types.Context):
    self.layout.operator(export_aqp.PSO2_OT_ExportAqp.bl_idname, text="PSO2 AQP (.aqp)")


def reload():
    bpy.ops.script.reload()


if ADDON_PATH.is_symlink():
    from . import watcher

    if "watch" not in locals():
        watch = watcher.FileWatcher(reload)

    if first_load:
        watch.start()
    else:
        watch.reset()

if __name__ == "__main__":
    register()
