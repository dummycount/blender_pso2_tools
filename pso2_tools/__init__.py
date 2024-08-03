bl_info = {
    "name": "PSO2 format",
    "version": (1, 3, 0),
    "blender": (3, 5, 0),
    "category": "Import-Export",
}


if "reloader" in locals():
    import importlib

    # pylint: disable=used-before-assignment
    importlib.reload(reloader)
    reloader.reload_addon(__name__)


import sysconfig
import sys

sys.path.append(sysconfig.get_path("platlib", "nt_user"))


import bpy
from . import classes, import_model, export_model, import_search, reloader


def register():
    classes.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    classes.unregister()


def menu_func_import(self: bpy.types.Operator, context: bpy.types.Context):
    self.layout.operator(import_model.ImportAqp.bl_idname, text="PSO2 Model (.aqp)")
    self.layout.operator(import_model.ImportIce.bl_idname, text="PSO2 ICE Archive")
    self.layout.operator(import_search.PSO2_OT_ModelSearch.bl_idname, text="PSO2 Item")


def menu_func_export(self: bpy.types.Operator, context: bpy.types.Context):
    self.layout.operator(export_model.ExportAqp.bl_idname, text="PSO2 Model (.aqp)")


if __name__ == "__main__":
    classes()
