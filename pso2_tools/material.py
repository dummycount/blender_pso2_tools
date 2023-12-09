from pathlib import Path
import tempfile
from typing import Iterable, Optional

import bpy

from .aqp_info import AqpInfo, AqpMaterial
from .colors import Colors
from .import_dds import dds_to_png
from .object_info import ObjectInfo
from .object_colors import ensure_color_channels_updated, get_object_color_channels
from .shaders.shader import MaterialTextures
from .shaders.ngs_default import NgsDefaultMaterial
from .shaders.ngs_eye import NgsEyeMaterial, NgsEyeTearMaterial
from .shaders.ngs_hair import NgsHairMaterial
from .shaders.ngs_skin import NgsSkinMaterial
from .shaders.classic import ClassicDefaultMaterial, is_classic_shader


def texture_has_part(name: str, parts: str | Iterable[str]):
    """
    Get whether any of the underscore-delimited parts of a texture name matches
    one of the given strings.
    """
    if isinstance(parts, str):
        parts = [parts]

    name = name.partition(".")[0]

    return any(x in parts for x in name.split("_"))


def delete_empty_images():
    for image in bpy.data.images.values():
        if image.size[0] == 0 and image.size[1] == 0:
            bpy.data.images.remove(image)


def load_textures(folder: Path, pattern="*.dds"):
    for texture in folder.rglob(pattern):
        load_image(texture)


def _load_dds(file: Path) -> bpy.types.Image:
    with tempfile.TemporaryDirectory() as tempdir:
        pngfile = Path(tempdir) / file.with_suffix(".png").name
        dds_to_png(str(file), str(pngfile))

        image = bpy.data.images.load(str(pngfile))
        image.name = file.name

        image.pack()

        return image


def load_image(file: Path) -> bpy.types.Image:
    """Load a PSO2 texture from a .png image"""

    if file.suffix == ".dds":
        image = _load_dds(file)
    else:
        image = bpy.data.images.load(str(file))
        image.pack()

    if texture_has_part(image.name, ("d")):
        image.colorspace_settings.is_data = False
        image.colorspace_settings.name = "sRGB"
    else:
        # Data textures (normal map, etc.)
        image.colorspace_settings.is_data = True
        image.colorspace_settings.name = "Non-Color"

    return image


def skin_material_exists(model_info: AqpInfo) -> bool:
    """Get whether a model contains a skin material"""

    return any(mat.shaders == ["1102p", "1102"] for mat in model_info.materials)


def update_materials(
    context: bpy.types.Context,
    names: Iterable[str],
    object_info: ObjectInfo,
    model_info: AqpInfo,
):
    """
    Take the materials with the given names which resulted from an FBX import
    and update them to approximate PSO2 shaders.
    """
    for name in names:
        update_material(context, bpy.data.materials[name], object_info, model_info)


def update_material(
    context: bpy.types.Context,
    mat: bpy.types.Material,
    object_info: ObjectInfo,
    model_info: AqpInfo,
):
    mat_info = model_info.get_fbx_material(mat.name)

    if mat_info:
        ensure_color_channels_updated(context)
        update_material_settings(mat, mat_info, object_info)

        if builder := _get_material_builder(mat, mat_info, object_info):
            builder.build(context)

    else:
        print("Failed to find material:", mat.name)
        print("Candidates:")
        for candidate in model_info.materials:
            print("  ", candidate.fbx_name)


def update_material_settings(
    mat: bpy.types.Material, mat_info: AqpMaterial, object_info: ObjectInfo
):
    if mat_info.blend_type in ("add", "blendalpha", "hollow"):
        if mat_info.alpha_cutoff > 0:
            mat.blend_method = "CLIP"
            mat.alpha_threshold = mat_info.alpha_cutoff / 256
        else:
            mat.blend_method = "HASHED" if object_info.is_hair else "BLEND"
            mat.show_transparent_back = False
    else:
        mat.blend_method = "OPAQUE"

    match mat_info.two_sided:
        case 0:
            mat.use_backface_culling = True

        case 1:
            mat.use_backface_culling = False

        case 2:
            # Not sure about this. Turning on backface culling fixes Z fighting
            # on some opaque models but makes some features of transparent
            # models disappear, so just enable it if not using alpha.
            mat.use_backface_culling = mat.blend_method != "blendalpha"


def get_textures(mat_info: AqpMaterial, *tags: str):
    if not tags:
        return MaterialTextures()

    return MaterialTextures(
        alpha=_find_texture(mat_info, tags, "a"),
        diffuse=_find_texture(mat_info, tags, "d"),
        multi=_find_texture(mat_info, tags, "m"),
        normal=_find_texture(mat_info, tags, "n"),
        specular=_find_texture(mat_info, tags, "s"),
        layer=_find_texture(mat_info, tags, "l"),
        texture_c=_find_texture(mat_info, tags, "c"),
        texture_g=_find_texture(mat_info, tags, "g"),
        texture_o=_find_texture(mat_info, tags, "o"),
        texture_p=_find_texture(mat_info, tags, "p"),
        texture_v=_find_texture(mat_info, tags, "v"),
    )


def _find_texture(
    mat_info: AqpMaterial, tags: Iterable[str], texture_type: str
) -> Optional[bpy.types.Image]:
    of_type = [
        img
        for img in bpy.data.images.values()
        if texture_has_part(img.name, texture_type) and texture_has_part(img.name, tags)
    ]

    if not of_type:
        return None

    # If there are multiple candidates, just pick the one that matches the
    # material name the closest I guess.
    return min(of_type, key=lambda img: levenshtein_dist(img.name, mat_info.name))


def levenshtein_dist(str0: str, str1: str):
    m = len(str0)
    n = len(str1)

    v0 = list(range(n + 1))
    v1 = [0] * (n + 1)

    for i in range(m):
        v1[0] = i + 1

        for j in range(n):
            deletion_cost = v0[j + 1] + 1
            insertion_cost = v1[j] + 1
            substitution_cost = v0[j] + (0 if str0[i] == str1[j] else 1)

            v1[j + 1] = min(deletion_cost, insertion_cost, substitution_cost)

        swap = v0
        v0 = v1
        v1 = swap

    return v0[n]


def _get_material_builder(
    mat: bpy.types.Material,
    mat_info: AqpMaterial,
    object_info: ObjectInfo = None,
):
    object_info = object_info or ObjectInfo()

    main_mats = []
    sub_mats = []
    colors = get_object_color_channels(object_info)

    # TODO: find textures based on textures list in mat_info instead of this
    match mat_info.special_type:
        case "pl":  # Classic outfit, cast body
            main_mats += ["bd", "tr"]

        case "fc":  # NGS face
            main_mats += ["rhd"]

        case "hr":  # Classic hair, some NGS hair parts
            main_mats += ["hr", "rhr"]
            if not colors:
                colors = [Colors.Hair1, Colors.Hair2]

        case "rhr":  # NGS Hair
            main_mats += ["rhr"]
            if not colors:
                colors = [Colors.Hair1, Colors.Hair2]

        case "rbd" | "rbd_d":  # NGS outfit, cast body
            main_mats += ["bw", "bd"]
            if not colors:
                if object_info.use_cast_colors:
                    colors = [Colors.Cast1, Colors.Cast2, Colors.Cast3, Colors.Cast4]
                else:
                    colors = [Colors.Base1, Colors.Base2]

        case "rbd_ou":  # NGS outerwear
            main_mats += ["ow"]
            if not colors:
                colors = [Colors.Outer1, Colors.Outer2]

        case _:
            main_mats += ["ah", "rac"]  # Classic or NGS accessory
            main_mats += ["wp"]  # Weapon
            main_mats += ["en"]  # Enemy

    match mat_info.name:
        case "eyebrow_mat":
            main_mats += ["reb"]  # NGS Eyebrow

        case "eyelash_mat":
            main_mats += ["res"]  # NGS Eyelash

        case "eye_l" | "eye_r" | "tear_l" | "tear_r":
            main_mats += ["rey"]

    # TODO: Unhandled shaders
    # 1106 - fur?
    # 1107 - eyelash? also used in some accessories
    # 1108 - eyebrow?
    # 1200 - enemy?
    # 1201 - enemy?
    # 1220 - enemy?
    # 1302 - weapon photon?
    # 1302 - weapon opaque?
    shader_pair = f"{mat_info.shaders[0]},{mat_info.shaders[1]}"
    match shader_pair:
        # Just use a generic classic shader for all values < 1000
        case name if is_classic_shader(name):
            return ClassicDefaultMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
            )

        case "1102p,1102":
            return NgsSkinMaterial(
                mat,
                skin_textures=get_textures(mat_info, "sk"),
                inner_textures=get_textures(mat_info, "iw", "rba"),
            )

        case "1103p,1103":
            return NgsHairMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
                colors=colors,
            )

        case "1104p,1104":
            return NgsEyeMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
                eye_index=1 if mat_info.name == "eye_r" else 0,
            )

        case "1105p,1105":
            return NgsEyeTearMaterial(mat)

        case _:  # 1100p,1100
            return NgsDefaultMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
                colors=colors,
                object_info=object_info,
            )
