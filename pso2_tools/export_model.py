from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable, cast

import bpy
from AquaModelLibrary.Core.General import AssimpModelImporter
from AquaModelLibrary.Data.PSO2.Aqua import AquaNode, AquaObject, AquaPackage
from io_scene_fbx import export_fbx_bin


def export(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    path: Path,
    is_ngs=True,
    overwrite_aqn=False,
    fbx_options: dict[str, Any] = None,
):
    fbx_options = fbx_options or {}

    with TemporaryDirectory() as tempdir:
        fbxfile = Path(tempdir) / path.with_suffix(".fbx").name

        # Make sure the armature is included for everything that will be exported,
        # or the exported FBX will convert to a broken AQP.
        with _include_parents(context, fbx_options):
            result = export_fbx_bin.save(
                operator, context, filepath=str(fbxfile), **fbx_options
            )

        if "FINISHED" not in result:
            return result

        AssimpModelImporter.scaleHandling = (
            AssimpModelImporter.ScaleHandling.CustomScale
        )
        AssimpModelImporter.customScale = 100

        # TODO: support exporting motions
        model, aqn = cast(
            tuple[AquaObject, AquaNode],
            AssimpModelImporter.AssimpAquaConvertFull(
                str(fbxfile), 1, False, is_ngs, AquaNode()
            ),
        )

    package = AquaPackage(model)
    package.WritePackage(str(path))

    aqn_path = path.with_suffix(".aqn")
    if overwrite_aqn or not aqn_path.exists():
        aqn_path.write_bytes(aqn.GetBytesNIFL())

    return {"FINISHED"}


@contextmanager
def _include_parents(context: bpy.types.Context, fbx_options: dict[str, Any]):
    shown_objects: set[bpy.types.Object] = set()
    viewport_shown_objects: set[bpy.types.Object] = set()

    use_visible = fbx_options.get("use_visible", False)
    use_selection = fbx_options.get("use_selection", False)

    if use_selection:
        ctx_objects = context.selected_objects
    else:
        ctx_objects = context.view_layer.objects

    try:
        # If we are only including visible objects, make sure the parents of any
        # visible objects are also visible.
        if use_visible:
            for obj in _get_visible_meshes(ctx_objects):
                while obj := obj.parent:
                    if obj.hide_get():
                        obj.hide_set(False)
                        shown_objects.add(obj)

                    if obj.hide_viewport:
                        obj.hide_viewport = False
                        viewport_shown_objects.add(obj)

        # If we are only including selected objects, make sure the parents of any
        # selected objects are also selected.
        if use_selection:
            selection = set(context.selected_objects)
            for obj in _get_selected_meshes(ctx_objects):
                while obj := obj.parent:
                    if not obj.select_get():
                        selection.add(obj)

            with context.temp_override(selected_objects=list(selection)):
                yield
        else:
            yield
    finally:
        for obj in shown_objects:
            obj.hide_set(True)

        for obj in viewport_shown_objects:
            obj.hide_viewport = True


def _get_visible_meshes(objects: Iterable[bpy.types.Object]):
    return (obj for obj in objects if obj.type == "MESH" and obj.visible_get())


def _get_selected_meshes(objects: Iterable[bpy.types.Object]):
    return (obj for obj in objects if obj.type == "MESH" and obj.select_get())
