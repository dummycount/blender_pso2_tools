from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, TypedDict, cast, get_type_hints

import bpy
from mathutils import Matrix

from . import dotnet, fbx_wrapper
from .util import OperatorResult


class FbxExportOptions(TypedDict, total=False):
    use_selection: bool
    use_visible: bool
    use_active_collection: bool
    collection: str

    global_matrix: Matrix
    apply_unit_scale: bool
    global_scale: float
    apply_scale_options: str
    axis_up: str
    axis_forward: str
    context_objects: Any
    object_types: Any
    use_mesh_modifiers: bool
    use_mesh_modifiers_render: bool
    mesh_smooth_type: str
    use_subsurf: bool
    use_armature_deform_only: bool
    bake_anim: bool
    bake_anim_use_all_bones: bool
    bake_anim_use_nla_strips: bool
    bake_anim_use_all_actions: bool
    bake_anim_step: float
    bake_anim_simplify_factor: float
    bake_anim_force_startend_keying: bool
    add_leaf_bones: bool
    primary_bone_axis: str
    secondary_bone_axis: str
    use_metadata: bool
    path_mode: str
    use_mesh_edges: bool
    use_tspace: bool
    use_triangles: bool
    embed_textures: bool
    use_custom_props: bool
    bake_space_transform: bool
    armature_nodetype: str
    colors_type: str
    prioritize_active_color: bool


class ExportOptions(FbxExportOptions, total=False):
    rigid: bool


def export(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    path: Path,
    is_ngs=True,
    overwrite_aqn=False,
    options: ExportOptions | None = None,
) -> OperatorResult:
    from AquaModelLibrary.Core.General import AssimpModelImporter
    from AquaModelLibrary.Data.PSO2.Aqua import AquaNode, AquaObject, AquaPackage

    dotnet.set_assimp_probing_paths()

    options = options or {}

    with TemporaryDirectory() as tempdir:
        fbxfile = Path(tempdir) / path.with_suffix(".fbx").name

        # Make sure the armature is included for everything that will be exported,
        # or the exported FBX will convert to a broken AQP.
        with _include_parents(context, options):
            fbx_options = _get_fbx_options(options)

            result = fbx_wrapper.save(
                operator, context, filepath=str(fbxfile), **fbx_options
            )

        if "FINISHED" not in result:
            return result

        AssimpModelImporter.scaleHandling = (
            AssimpModelImporter.ScaleHandling.FileScaling
        )

        # TODO: support exporting motions
        model, aqn = cast(
            "tuple[AquaObject, AquaNode]",
            AssimpModelImporter.AssimpAquaConvertFull(
                initialFilePath=str(fbxfile),
                scaleFactor=1,
                preAssignNodeIds=False,
                isNGS=is_ngs,
                aqn=AquaNode(),
                rigidImport=options.get("rigid", False),
            ),
        )

    package = AquaPackage(model)
    package.WritePackage(str(path))

    aqn_path = path.with_suffix(".aqn")
    if overwrite_aqn or not aqn_path.exists():
        aqn_path.write_bytes(aqn.GetBytesNIFL())  # type: ignore

    return {"FINISHED"}


@contextmanager
def _include_parents(context: bpy.types.Context, fbx_options: ExportOptions):
    shown_objects: set[bpy.types.Object] = set()
    viewport_shown_objects: set[bpy.types.Object] = set()

    use_visible = fbx_options.get("use_visible", False)
    use_selection = fbx_options.get("use_selection", False)

    if use_selection:
        ctx_objects = context.selected_objects
    else:
        assert context.view_layer is not None
        ctx_objects = context.view_layer.objects

    if ctx_objects is None:
        raise TypeError()

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
            selection = set(context.selected_objects or [])
            for obj in _get_selected_meshes(ctx_objects):
                while obj := obj.parent:
                    if not obj.select_get():
                        selection.add(obj)

            with context.temp_override(selected_objects=list(selection)):  # type: ignore
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


def _get_fbx_options(options: ExportOptions):
    result = FbxExportOptions()

    for key in get_type_hints(FbxExportOptions):
        if key in options:
            result[key] = options[key]

    return result
