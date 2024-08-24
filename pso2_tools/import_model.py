from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory
from typing import Iterable, Optional

import bpy
import System
from AquaModelLibrary.Core.General import FbxExporterNative
from AquaModelLibrary.Data.PSO2.Aqua import AquaMotion, AquaNode, AquaPackage
from io_scene_fbx import import_fbx
from System.Collections.Generic import List
from System.Numerics import Matrix4x4

from . import colors, ice, material, objects, shaders
from .preferences import get_preferences


def import_object(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    obj: objects.CmxObjectBase,
    high_quality=True,
    automatic_bone_orientation=False,
):
    data_path = get_preferences(context).get_pso2_data_path()

    texture_names = obj.get_textures()
    print("Importing model with textures", texture_names)

    files = obj.get_files()
    ice_paths = [p for f in files if (p := _get_ice_path(f, data_path, high_quality))]

    color_map = obj.get_color_map()
    uv_map = None

    if isinstance(obj, objects.CmxBodyObject):
        uv_map = _get_uv_map(obj)

    import_ice_files(
        operator,
        context,
        ice_paths,
        automatic_bone_orientation=automatic_bone_orientation,
        high_quality=high_quality,
        use_t2_skin=obj.is_t2,
        color_map=color_map,
        uv_map=uv_map,
    )


@dataclass
class IceFileContents:
    texture_files: list[ice.DataFile] = field(default_factory=list)
    model_files: list[ice.DataFile] = field(default_factory=list)
    node_files: list[ice.DataFile] = field(default_factory=list)


def collect_ice_contents(paths: Iterable[Path]):
    result = IceFileContents()

    for path in paths:
        icefile = ice.IceFile.load(path)
        for data in icefile.group_two:
            match Path(data.name).suffix:
                case ".aqp":
                    result.model_files.append(data)

                case ".aqn":
                    result.node_files.append(data)

                case ".dds":
                    result.texture_files.append(data)

    return result


def import_ice_files(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    paths: Iterable[Path],
    automatic_bone_orientation=False,
    high_quality=True,
    use_t2_skin=False,
    color_map: Optional[colors.ColorMapping] = None,
    uv_map: Optional[material.UVMapping] = None,
):

    files = collect_ice_contents(paths)

    original_mat_keys = set(bpy.data.materials.keys())
    materials: list[material.Material] = []

    for model in files.model_files:
        # TODO: for linked outerwear, just get the material info from the model
        # but don't import the model.
        print("Importing", model.name)
        name = model.name.removesuffix(".aqp")
        aqn = next(
            (f for f in files.node_files if f.name.removesuffix(".aqn") == name), None
        )

        result = import_aqp(
            operator,
            context,
            model,
            aqn,
            automatic_bone_orientation=automatic_bone_orientation,
        )
        materials.extend(result)

    new_mat_keys = set(bpy.data.materials.keys()).difference(original_mat_keys)

    model_materials = material.ModelMaterials(
        materials={
            key: mat
            for key in new_mat_keys
            if (mat := material.find_material(key, materials))
        },
        textures=[import_ice_image(tex) for tex in files.texture_files],
    )

    model_materials.create_custom_properties(context)

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

    # TODO: update new_mats with PSO2 shader materials.

    delete_empty_images()

    pprint(model_materials.materials)
    print(model_materials.extra_textures)

    for key, mat in model_materials.materials.items():
        data = shaders.types.ShaderData(
            material=mat,
            textures=model_materials.get_textures(mat),
            color_map=color_map or colors.ColorMapping(),
            uv_map=uv_map,
        )
        shaders.build_material(context, bpy.data.materials[key], data)


def _get_ice_path(filename: objects.CmxFileName, data_path: Path, high_quality: bool):
    if high_quality and (path := filename.ex.path(data_path)):
        return path

    if path := filename.path(data_path):
        return path

    return None


def delete_empty_images():
    for image in bpy.data.images.values():
        if image.size[0] == 0 and image.size[1] == 0:
            bpy.data.images.remove(image)


def import_ice_image(data: ice.DataFile):
    print("Importing", data.name)

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
        image.colorspace_settings.name = "sRGB"
    else:
        # Data textures (normal map, etc.)
        image.colorspace_settings.is_data = True
        image.colorspace_settings.name = "Non-Color"

    return image


def import_aqp(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    aqp: Path | ice.DataFile,
    aqn: Path | ice.DataFile | None,
    automatic_bone_orientation=False,
):
    if isinstance(aqp, Path):
        aqp_data = aqp.read_bytes()
        aqp_name = aqp.name
    else:
        aqp_data = aqp.data
        aqp_name = aqp.name

    package = AquaPackage(aqp_data)
    model = package.models[0]

    if aqn is not None:
        aqn_data = aqn.read_bytes() if isinstance(aqn, Path) else aqn.data
        skeleton = AquaNode(aqn_data)
    else:
        skeleton = AquaNode.GenerateBasicAQN()

    _remove_invalid_bones(model, skeleton)

    if model.objc.type > 0xC32:
        model.splitVSETPerMesh()

    model.FixHollowMatNaming()

    # TODO: support importing motion files
    aqms = List[AquaMotion]()
    aqm_names = List[System.String]()
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
            instance_transforms,
            include_metadata,
        )

        import_fbx.load(
            operator,
            context,
            filepath=str(fbxfile),
            automatic_bone_orientation=automatic_bone_orientation,
        )

    mesh_mat_mapping = List[int]()
    materials, _ = model.GetUniqueMaterials(mesh_mat_mapping)

    return [material.Material.from_generic_material(mat) for mat in materials]


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
    ice_paths = [p for f in files if (p := _get_ice_path(f, data_path, high_quality))]

    skin_textures = collect_ice_contents(ice_paths).texture_files

    return [import_ice_image(tex) for tex in skin_textures]


def _get_uv_map(obj: objects.CmxBodyObject):
    match obj.object_type:
        case objects.ObjectType.CAST_ARMS:
            return material.CAST_ARMS_UV_MAPPING
        case objects.ObjectType.CAST_BODY:
            return material.CAST_BODY_UV_MAPPING
        case objects.ObjectType.CAST_LEGS:
            return material.CAST_LEGS_UV_MAPPING
        case _:
            return None
