"""
PSO2 Tools Blender addon
"""

# ruff: noqa: E402
import bpy

bl_info = {
    "name": "PSO2 Tools",
    "version": (2, 7, 0),
    "blender": (4, 4, 0),
    "category": "Import-Export",
}

if "reloader" in locals():
    import importlib

    # ruff: disable[F821]
    importlib.reload(reloader)
    reloader.reload_addon(__name__)  # type: ignore
    # ruff: enable[F821]

from . import (
    classes,
    dotnet,
    export_aqp,
    import_aqp,
    import_ice,
    import_search,
    operators,
    scene_props,
)
from . import reloader as reloader
from .panels import appearance as appearance
from .panels import mesh as mesh
from .panels import ornaments as ornaments
from .paths import ADDON_PATH


def register():
    dotnet.load()

    classes.bpy_register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_edit_armature_names.append(operators.rename_bones.menu_func)

    scene_props.add_custom_properties()


def unregister():
    # TODO: unload pythonnet when the extension is disabled.
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_edit_armature_names.remove(operators.rename_bones.menu_func)
    classes.bpy_unregister()


def menu_func_import(self: bpy.types.Operator, context: bpy.types.Context):
    assert self.layout is not None

    self.layout.operator(import_aqp.PSO2_OT_ImportAqp.bl_idname, text="PSO2 AQP (.aqp)")
    self.layout.operator(
        import_ice.PSO2_OT_ImportIce.bl_idname, text="PSO2 ICE Archive"
    )
    self.layout.operator(
        import_search.PSO2_OT_ModelSearch.bl_idname, text="PSO2 Model Search"
    )


def menu_func_export(self: bpy.types.Operator, context: bpy.types.Context):
    assert self.layout is not None

    self.layout.operator(export_aqp.PSO2_OT_ExportAqp.bl_idname, text="PSO2 AQP (.aqp)")


if ADDON_PATH.is_symlink():
    from . import watcher

    if "watch" in locals():
        watch.reset()  # noqa: F821 # type: ignore
    else:
        watch = watcher.FileWatcher(bpy.ops.script.reload)
        watch.start()
