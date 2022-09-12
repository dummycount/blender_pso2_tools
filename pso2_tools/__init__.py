bl_info = {
    "name": "PSO2 format",
    "version": (1, 0, 0),
    "blender": (3, 2, 0),
    "category": "Import-Export",
}


if "bpy" in locals():
    import importlib

    if "classes" in locals():
        importlib.reload(classes)
    if "import_model" in locals():
        importlib.reload(import_model)
    if "export_model" in locals():
        importlib.reload(export_model)
    if "preferences" in locals():
        importlib.reload(preferences)

import bpy
from . import classes, import_model, export_model, preferences


def register():
    classes.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    classes.unregister()


def menu_func_import(self, context):
    self.layout.operator(import_model.ImportAqp.bl_idname, text="PSO2 Model (.aqp)")
    self.layout.operator(import_model.ImportIce.bl_idname, text="PSO2 ICE Archive")


def menu_func_export(self, context):
    self.layout.operator(export_model.ExportAqp.bl_idname, text="PSO2 Model (.aqp)")


if __name__ == "__main__":
    classes()
