import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

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
    fbx_options=None,
):
    # TODO: if fbx_options has use_selection or use_visible set, then temporarily
    # select or make visible all armatures used by visible/selected meshes, or
    # this will generate a broken AQP file.

    with TemporaryDirectory() as tempdir:
        fbxfile = Path(tempdir) / path.with_suffix(".fbx").name

        result = export_fbx_bin.save(
            operator, context, filepath=str(fbxfile), **fbx_options
        )
        if result != {"FINISHED"}:
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
