from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Iterable, Optional

import bpy

from .aqp_info import AqpInfo, AqpMaterial
from .object_info import ObjectInfo
from .import_dds import dds_to_png
from .shaders import default_colors
from .shaders.shader import Color, ColorGroup, MaterialTextures
from .shaders.ngs_default import NgsDefaultMaterial
from .shaders.ngs_eye import NgsEyeMaterial, NgsEyeTearMaterial
from .shaders.ngs_hair import NgsHairMaterial
from .shaders.ngs_skin import NgsSkinMaterial
from .shaders.classic import ClassicDefaultMaterial, is_classic_shader


@dataclass
class CustomColors:
    custom_color_1: Color = default_colors.BASE_COLOR_1
    custom_color_2: Color = default_colors.BASE_COLOR_2
    custom_color_3: Color = default_colors.BASE_COLOR_3
    custom_color_4: Color = default_colors.BASE_COLOR_4
    main_skin_color: Color = default_colors.MAIN_SKIN_COLOR
    sub_skin_color: Color = default_colors.SUB_SKIN_COLOR
    inner_color_1: Color = default_colors.INNER_COLOR_1
    inner_color_2: Color = default_colors.INNER_COLOR_2
    hair_color_1: Color = default_colors.HAIR_COLOR_1
    hair_color_2: Color = default_colors.HAIR_COLOR_2
    eye_color: Color = default_colors.EYE_COLOR

    @property
    def group_basewear(self):
        return ColorGroup(
            "PSO2 Basewear Colors",
            [("Color 1", self.custom_color_1), ("Color 2", self.custom_color_2)],
        )

    @property
    def group_innerwear(self):
        return ColorGroup(
            "PSO2 Innerwear Colors",
            [("Color 1", self.inner_color_1), ("Color 2", self.inner_color_2)],
        )

    @property
    def group_cast_part(self):
        return ColorGroup(
            "PSO2 Cast Colors",
            [
                ("Color 1", self.custom_color_1),
                ("Color 2", self.custom_color_2),
                ("Color 3", self.custom_color_3),
                ("Color 4", self.custom_color_4),
            ],
        )

    @property
    def group_skin(self):
        return ColorGroup(
            "PSO2 Skin Colors",
            [("Main", self.main_skin_color), ("Sub", self.sub_skin_color)],
        )

    @property
    def group_hair(self):
        return ColorGroup(
            "PSO2 Hair Colors",
            [("Color 1", self.hair_color_1), ("Color 2", self.hair_color_2)],
        )

    @property
    def group_eyes(self):
        return ColorGroup(
            "PSO2 Eye Colors",
            [("Left", self.eye_color), ("Right", self.eye_color)],
        )

    @property
    def group_classic_outfit(self):
        return ColorGroup(
            "PSO2 Classic Colors",
            [("Skin", self.main_skin_color), ("Outfit", self.custom_color_1)],
        )


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

    if texture_has_part(image.name, ("l", "m", "n", "o", "s")):
        # Data textures (normal map, etc.)
        image.colorspace_settings.is_data = True
        image.colorspace_settings.name = "Non-Color"

    return image


def skin_material_exists(model_info: AqpInfo) -> bool:
    """Get whether a model contains a skin material"""

    return any(mat.special_type == "rbd_sk" for mat in model_info.materials)


def update_materials(
    names: Iterable[str],
    colors: CustomColors,
    object_info: ObjectInfo,
    model_info: AqpInfo,
):
    """
    Take the materials with the given names which resulted from an FBX import
    and update them to approximate PSO2 shaders.
    """
    for name in names:
        update_material(bpy.data.materials[name], colors, object_info, model_info)


def update_material(
    mat: bpy.types.Material,
    colors: CustomColors,
    object_info: ObjectInfo,
    model_info: AqpInfo,
):
    mat_info = model_info.get_fbx_material(mat.name)

    if mat_info:
        update_material_settings(mat, mat_info, object_info)

        if builder := _get_material_builder(mat, mat_info, colors, object_info):
            builder.build()

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
            mat.blend_method = "HASHED" if object_info.is_hair_object else "BLEND"
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
    colors: CustomColors = None,
    object_info: ObjectInfo = None,
):
    colors = colors or CustomColors()
    object_info = object_info or ObjectInfo()

    main_mats = []
    sub_mats = []
    shader_colors = colors.group_basewear

    # TODO: find textures based on textures list in mat_info instead of this
    # TODO: set shader colors according to object_info instead of mat_info
    match mat_info.special_type:
        case "pl":  # Classic outfit, cast body
            main_mats += ["bd", "tr"]
            shader_colors = colors.group_classic_outfit

        case "fc":  # NGS face
            main_mats += ["rhd"]
            shader_colors = colors.group_classic_outfit

        case "hr":  # Classic hair, some NGS hair parts
            main_mats += ["hr", "rhr"]
            shader_colors = colors.group_hair

        case "rhr":  # NGS Hair
            main_mats += ["rhr"]
            shader_colors = colors.group_hair

        case "rbd" | "rbd_d":  # NGS outfit, cast body
            main_mats += ["bw", "bd"]
            shader_colors = (
                colors.group_cast_part
                if object_info.use_cast_colors
                else colors.group_basewear
            )

        case "rbd_ou":  # NGS outerwear
            main_mats += ["ow"]
            shader_colors = colors.group_basewear

        case "rbd_sk":  # NGS body skin + innerwear
            main_mats += ["sk"]
            sub_mats += ["iw", "rba"]
            shader_colors = colors.group_skin

        case _:
            main_mats += ["ah", "rac"]  # Classic or NGS accessory
            main_mats += ["wp"]  # Weapon
            main_mats += ["en"]  # Enemy

    match mat_info.name:
        case "eyebrow_mat":
            main_mats += ["reb"]  # NGS Eyebrow
            shader_colors = colors.group_hair

        case "eyelash_mat":
            main_mats += ["res"]  # NGS Eyelash
            shader_colors = colors.group_hair

        case "eye_l" | "eye_r" | "tear_l" | "tear_r":
            main_mats += ["rey"]
            shader_colors = colors.group_eyes

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
                colors=shader_colors,
            )

        case "1102p,1102":
            return NgsSkinMaterial(
                mat,
                skin_textures=get_textures(mat_info, *main_mats),
                inner_textures=get_textures(mat_info, *sub_mats),
                skin_colors=shader_colors,
                inner_colors=colors.group_innerwear,
            )

        case "1103p,1103":
            return NgsHairMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
                colors=shader_colors,
            )

        case "1104p,1104":
            return NgsEyeMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
                colors=shader_colors,
                eye_index=1 if mat_info.name == "eye_r" else 0,
            )

        case "1105p,1105":
            return NgsEyeTearMaterial(mat)

        case _:  # 1100p,1100
            return NgsDefaultMaterial(
                mat,
                textures=get_textures(mat_info, *main_mats),
                colors=shader_colors,
                object_info=object_info,
            )
