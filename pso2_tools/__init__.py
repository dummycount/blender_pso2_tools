"""
PSO2 Tools Blender addon
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
import sys
import traceback

from .paths import BIN_PATH

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


from . import classes, object_database, reloader, watcher


def register():
    classes.bpy_register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    # TODO: do this when requested instead of at startup
    try:
        db = object_database.ObjectDatabase(bpy.context)
        db.update_database()
    except Exception:
        print(traceback.format_exc())


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    classes.bpy_unregister()


def menu_func_import(self: bpy.types.Operator, context: bpy.types.Context):
    pass
    # self.layout.operator(import_model.ImportAqp.bl_idname, text="PSO2 Model (.aqp)")
    # self.layout.operator(import_model.ImportIce.bl_idname, text="PSO2 ICE Archive")
    # self.layout.operator(import_search.PSO2_OT_ModelSearch.bl_idname, text="PSO2 Item")


def menu_func_export(self: bpy.types.Operator, context: bpy.types.Context):
    pass
    # self.layout.operator(export_model.ExportAqp.bl_idname, text="PSO2 Model (.aqp)")


def reload():
    print("RELOAD!")
    bpy.ops.script.reload()


# TODO: disable this in release versions (test if module directory is a symlink?)
if "watch" not in locals():
    watch = watcher.FileWatcher(reload)

if first_load:
    watch.start()
else:
    watch.reset()

if __name__ == "__main__":
    register()
