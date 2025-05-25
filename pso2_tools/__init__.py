"""
PSO2 Tools Blender addon
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
import bpy

bl_info = {
    "name": "PSO2 Tools",
    "version": (2, 4, 1),
    "blender": (4, 4, 0),
    "category": "Import-Export",
}

if "reloader" in locals():
    import importlib

    # pylint: disable=used-before-assignment
    importlib.reload(reloader)  # type: ignore
    reloader.reload_addon(__name__)  # type: ignore

from . import dotnet

dotnet.load()

from . import (
    classes,
    export_aqp,
    import_aqp,
    import_ice,
    import_search,
    reloader,
    scene_props,
)
from .panels import appearance, ornaments
from .paths import ADDON_PATH


def register():
    classes.bpy_register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    scene_props.add_scene_properties()
    scene_props.add_material_properties()


def unregister():
    # TODO: unload pythonnet when the extension is disabled.
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


if ADDON_PATH.is_symlink():
    from . import watcher

    if "watch" in locals():
        # pylint: disable-next=used-before-assignment
        watch.reset()  # pyright: ignore[reportUndefinedVariable]
    else:
        watch = watcher.FileWatcher(bpy.ops.script.reload)
        watch.start()
