"""
PSO2 Tools Blender addon
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
from . import reloader

bl_info = {
    "name": "PSO2 Tools",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib

    # pylint: disable=used-before-assignment
    importlib.reload(reloader)
    reloader.reload_addon(__name__)

from pathlib import Path
import sys
import bpy

from . import classes, watcher
from pythonnet import load

load("coreclr")

import clr

# Blender complains about this, but there's no other way to get pythonnet
# to find the assemblies.
BIN_PATH = str(Path(__file__).parent / "bin")
if BIN_PATH not in sys.path:
    sys.path.append(BIN_PATH)

# pylint: disable=no-member
clr.AddReference("AquaModelLibrary.Core")
clr.AddReference("AquaModelLibrary.Data")
clr.AddReference("AquaModelLibrary.Helpers")
clr.AddReference("ZamboniLib")
# pylint: enable=no-member


def register():
    classes.bpy_register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


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
    unregister()
    reloader.reload_addon(__name__)
    register()


# TODO: disable this in release versions (test if module directory is a symlink?)
watcher = watcher.FileWatcher(reload)
watcher.start()

if __name__ == "__main__":
    register()
