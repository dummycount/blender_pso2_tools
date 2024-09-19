from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Optional

import bpy
from AquaModelLibrary.Core.General import FbxExporterNative
from AquaModelLibrary.Data.PSO2.Aqua import AquaPackage  # type: ignore
from AquaModelLibrary.Data.PSO2.Aqua import AquaMotion, AquaNode
from AquaModelLibrary.Data.Utility import CoordSystem
from io_scene_fbx import import_fbx
from System.Collections.Generic import List
from System.Numerics import Matrix4x4

from . import (
    colors,
    datafile,
    ice,
    material,
    objects,
    objects_aqp,
    scene_props,
    shaders,
)
from .debug import debug_pprint, debug_print
from .preferences import get_preferences


def import_object(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    obj: objects.CmxObjectBase,
    high_quality=True,
    fbx_options=None,
):
    debug_print("Importing object:", obj.name)

    data_path = get_preferences(context).get_pso2_data_path()

    files = obj.get_files()
    ice_files = [
        ice.IceFile.load(p)
        for f in files
        if (p := _get_ice_path(f, data_path, high_quality))
    ]

    options = _get_import_options(obj)

    return _import_models(
        operator,
        context,
        ice_files,
        high_quality=high_quality,
        fbx_options=fbx_options,
        **options,
    )


def import_ice_file(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    path: Path,
    fbx_options=None,
):
    debug_print("Importing ICE:", path.name)

    file_hash = path.name
    high_quality = True
    options = {}

    # TODO: if this fails, check the ICE file for an AQP and use guess_aqp_object()
    with closing(objects.ObjectDatabase(context)) as db:
        if obj := next(db.get_all(file_hash=file_hash), None):
            debug_print(
                f'Found matching hash. Importing with options from "{obj.name}"'
            )
            options = _get_import_options(obj)

            if isinstance(obj, objects.CmxObjectWithFile):
                high_quality = file_hash == obj.file.ex.hash

    return _import_models(
        operator,
        context,
        [ice.IceFile.load(path)],
        fbx_options=fbx_options,
        high_quality=high_quality,
        **options,
    )


def import_aqp_file(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    path: Path,
    fbx_options=None,
):
    debug_print("Importing AQP:", path.name)

    options = {}

    if obj := objects_aqp.guess_aqp_object(path.name, context):
        debug_print(f'Found matching object. Importing with options from "{obj.name}"')
        options = _get_import_options(obj)

    return _import_models(
        operator,
        context,
        [objects_aqp.AqpDataFileSource(path)],
        fbx_options=fbx_options,
        high_quality=True,
        **options,
    )


def _get_import_options(obj: objects.CmxObjectBase):
    color_map = obj.get_color_map()
    uv_map = None

    if isinstance(obj, objects.CmxBodyObject):
        uv_map = _get_uv_map(obj)

    return {
        "use_t2_skin": obj.is_t2,
        "color_map": color_map,
        "uv_map": uv_map,
    }


@dataclass
class ModelFiles:
    texture_files: list[datafile.DataFile] = field(default_factory=list)
    model_files: list[datafile.DataFile] = field(default_factory=list)
    node_files: list[datafile.DataFile] = field(default_factory=list)


def collect_model_files(sources: Iterable[datafile.DataFileSource]):
    result = ModelFiles()

    for source in sources:
        result.model_files.extend(source.glob("*.aqp"))
        result.node_files.extend(source.glob("*.aqn"))
        result.texture_files.extend(source.glob("*.dds"))

    return result


def _import_models(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    sources: Iterable[datafile.DataFileSource],
    fbx_options=None,
    high_quality=True,
    use_t2_skin=False,
    color_map: Optional[colors.ColorMapping] = None,
    uv_map: Optional[material.UVMapping] = None,
):
    debug_print(f"Import options: {high_quality=} {use_t2_skin=} {color_map=}")
    debug_print(f"FBX options: {fbx_options=}")

    files = collect_model_files(sources)

    original_mat_keys = set(bpy.data.materials.keys())
    materials: list[material.Material] = []

    for model in files.model_files:
        debug_print("Importing", model.name)
        name = model.name.removesuffix(".aqp")
        aqn = next(
            (f for f in files.node_files if f.name.removesuffix(".aqn") == name), None
        )

        result, new_materials = _import_aqp(
            operator,
            context,
            model,
            aqn,
            fbx_options=fbx_options,
        )
        if "FINISHED" not in result:
            return result

        materials.extend(new_materials)

    new_mat_keys = set(bpy.data.materials.keys()).difference(original_mat_keys)

    model_materials = material.ModelMaterials(
        materials={
            key: mat
            for key in new_mat_keys
            if (mat := material.find_material(key, materials))
        },
        textures=[import_data_image(tex) for tex in files.texture_files],
    )

    scene_props.add_scene_properties()
    scene_props.add_material_properties()

    # Collect extra textures that are not part of the model but are used by it.
    if model_materials.has_skin_material:
        model_materials.skin_textures = material.find_textures("rbd", "sk")
        if not model_materials.skin_textures:
            model_materials.skin_textures = _import_skin_textures(
                context, high_quality, use_t2_skin
            )

        if not model_materials.has_linked_inner_textures:
            model_materials.extra_textures.extend(material.find_textures("rbd", "iw"))

    if model_materials.has_eye_material:
        model_materials.extra_textures.extend(material.find_textures("rey"))

    if model_materials.has_eyebrow_material:
        model_materials.extra_textures.extend(material.find_textures("reb"))

    if model_materials.has_eyelash_material:
        model_materials.extra_textures.extend(material.find_textures("res"))

    if model_materials.has_classic_default_material:
        model_materials.extra_textures.extend(material.find_textures("bd", "iw"))

    if model_materials.has_decal_texture:
        model_materials.extra_textures.extend(material.find_textures("bp"))

    _delete_empty_images()

    debug_print("IMPORT MATERIALS:")
    debug_pprint(model_materials.materials)

    for key, mat in model_materials.materials.items():
        data = shaders.types.ShaderData(
            material=mat,
            textures=model_materials.get_textures(mat),
            color_map=color_map or colors.ColorMapping(),
            uv_map=uv_map,
        )
        shaders.build_material(context, bpy.data.materials[key], data)

    return {"FINISHED"}


def _get_ice_path(filename: objects.CmxFileName, data_path: Path, high_quality: bool):
    if high_quality and (path := filename.ex.path(data_path)):
        return path

    if path := filename.path(data_path):
        return path

    return None


def _delete_empty_images():
    for image in bpy.data.images.values():
        if image.size[0] == 0 and image.size[1] == 0:
            bpy.data.images.remove(image)


def import_data_image(data: datafile.DataFile):
    with TemporaryDirectory() as tempdir:
        tempfile = Path(tempdir) / data.name

        with tempfile.open("wb") as f:
            f.write(data.data)

        return import_image(tempfile)


def import_image(path: Path):
    image = bpy.data.images.load(str(path))
    image.pack()

    if material.texture_has_parts(image.name, "d"):
        # Diffuse texture
        image.colorspace_settings.is_data = False
        image.colorspace_settings.name = "sRGB"  # type: ignore
    else:
        # Data textures (normal map, etc.)
        image.colorspace_settings.is_data = True
        image.colorspace_settings.name = "Non-Color"  # type: ignore

    return image


def _import_aqp(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    aqp: Path | datafile.DataFile,
    aqn: Path | datafile.DataFile | None,
    fbx_options=None,
) -> tuple[set[str], list[material.Material]]:
    fbx_options = fbx_options or {}

    if isinstance(aqp, Path):
        aqp_data = aqp.read_bytes()
        aqp_name = aqp.name
    else:
        aqp_data = aqp.data
        aqp_name = aqp.name

    package = AquaPackage(aqp_data)
    model = package.models[0]

    # TODO: for linked outerwear, just get the material info from the model
    # but don't import the model.

    if aqn is not None:
        aqn_data = aqn.read_bytes() if isinstance(aqn, Path) else aqn.data
        skeleton = AquaNode(aqn_data)  # type: ignore
    else:
        skeleton = AquaNode.GenerateBasicAQN()

    _remove_invalid_bones(model, skeleton)

    if model.objc.type > 0xC32:
        model.splitVSETPerMesh()

    model.FixHollowMatNaming()

    # TODO: support importing motion files
    aqms = List[AquaMotion]()
    aqm_names = List[str]()
    instance_transforms = List[Matrix4x4]()
    include_metadata = True

    with TemporaryDirectory() as tempdir:
        fbxfile = Path(tempdir) / Path(aqp_name).with_suffix(".fbx")

        FbxExporterNative.ExportToFile(
            model,
            skeleton,
            aqms,
            str(fbxfile),
            aqm_names,
            instance_transforms,  # type: ignore
            include_metadata,
            int(CoordSystem.OpenGL),
        )

        result = import_fbx.load(
            operator,
            context,
            filepath=str(fbxfile),
            **fbx_options,
        )
        if result != {"FINISHED"}:
            return result, []

        if get_preferences(context).hide_armature:
            for obj in context.selected_objects:
                if obj.type == "ARMATURE":
                    obj.hide_set(True)

    mesh_mat_mapping = List[int]()
    generic_materials, _ = model.GetUniqueMaterials(mesh_mat_mapping)

    materials = [
        material.Material.from_generic_material(mat) for mat in generic_materials
    ]

    return {"FINISHED"}, materials


def _remove_invalid_bones(model: AquaPackage, skeleton: AquaNode):
    # TODO
    # model.bonePalette = model.bonePalette.Where(index => index < skeleton.nodeList.Count).ToList();
    pass


def _import_skin_textures(
    context: bpy.types.Context, high_quality: bool, use_t2_skin: bool
) -> list[bpy.types.Image]:
    preferences = get_preferences(context)
    data_path = preferences.get_pso2_data_path()

    skin_id = int(
        preferences.default_skin_t2 if use_t2_skin else preferences.default_skin_t1
    )

    with closing(objects.ObjectDatabase(context)) as db:
        result = db.get_skins(item_id=skin_id)

    if not result:
        return []

    skin = result[0]
    files = skin.get_files()
    ice_files = [
        ice.IceFile.load(p)
        for f in files
        if (p := _get_ice_path(f, data_path, high_quality))
    ]

    skin_textures = collect_model_files(ice_files).texture_files

    return [import_data_image(tex) for tex in skin_textures]


def _get_uv_map(obj: objects.CmxBodyObject):
    match (obj.is_ngs, obj.object_type):
        case True, objects.ObjectType.CAST_ARMS:
            return material.NGS_CAST_ARMS_UV
        case True, objects.ObjectType.CAST_BODY:
            return material.NGS_CAST_BODY_UV
        case True, objects.ObjectType.CAST_LEGS:
            return material.NGS_CAST_LEGS_UV

        case False, objects.ObjectType.CAST_ARMS:
            return material.CLASSIC_CAST_ARMS_UV
        case False, objects.ObjectType.CAST_BODY:
            return material.CLASSIC_CAST_BODY_UV
        case False, objects.ObjectType.CAST_LEGS:
            return material.CLASSIC_CAST_LEGS_UV

        case _:
            return None
