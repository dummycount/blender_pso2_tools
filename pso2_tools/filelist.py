from collections import defaultdict
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import bpy

from .metadata import FILE_LIST_DIR
from .object_category import Category
from .object_info import ModelPart, ObjectType
from .preferences import get_preferences

VARIANT_HIGH_QUALITY = "High Quality"
VARIANT_NORMAL_QUALITY = "Normal Quality"
VARIANT_REPLACEMENT = "Replacement"


@dataclass
class FileGroup:
    category: Category
    name: str
    object_type: Optional[ObjectType] = None
    object_id: int = 0
    part: Optional[ModelPart] = None
    files: defaultdict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    @property
    def variants(self):
        return list(self.files.keys())


FileTuple = tuple[Category, str, ObjectType | None, ModelPart | None]

_NGS_PLAYER_FILES: list[FileTuple] = [
    (Category.NgsHeadPart, "AllFacesNGS.csv", ObjectType.NGS_HEAD, None),
    (Category.NgsHeadPart, "AllHairNGS.csv", ObjectType.NGS_HAIR, None),
    (Category.NgsHeadPart, "EarsNGS.csv", ObjectType.NGS_EAR, None),
    (Category.NgsHeadPart, "EyebrowsNGS.csv", ObjectType.NGS_EYEBROW, None),
    (Category.NgsHeadPart, "EyelashesNGS.csv", ObjectType.NGS_EYELASHES, None),
    (Category.NgsHeadPart, "EyesNGS.csv", ObjectType.NGS_EYE, None),
    (Category.NgsHeadPart, "FacePaintNGS.csv", ObjectType.NGS_FACE_PAINT, None),
    (Category.NgsHeadPart, "HornsNGS.csv", ObjectType.NGS_HORN, None),
    (Category.NgsHeadPart, "TeethNGS.csv", ObjectType.NGS_TEETH, None),
    (
        Category.NgsCastPart,
        "CasealArmsNGS.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_CAST_ARMS,
    ),
    (
        Category.NgsCastPart,
        "CasealLegsNGS.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_CAST_LEGS,
    ),
    (
        Category.NgsCastPart,
        "CasealNGSBodies.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_CAST_BODY,
    ),
    (
        Category.NgsCastPart,
        "CastArmsNGS.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_CAST_ARMS,
    ),
    (
        Category.NgsCastPart,
        "CastLegsNGS.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_CAST_LEGS,
    ),
    (
        Category.NgsCastPart,
        "CastNGSBodies.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_CAST_BODY,
    ),
    (
        Category.NgsOutfit,
        "FemaleNGSBasewear.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_BASEWEAR,
    ),
    (
        Category.NgsOutfit,
        "FemaleNGSInnerwear.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_INNERWEAR,
    ),
    (
        Category.NgsOutfit,
        "FemaleNGSOuters.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_OUTERWEAR,
    ),
    (
        Category.NgsOutfit,
        "GenderlessNGSBasewear.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_BASEWEAR,
    ),
    (
        Category.NgsOutfit,
        "MaleNGSBasewear.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_BASEWEAR,
    ),
    (
        Category.NgsOutfit,
        "MaleNGSInnerwear.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_INNERWEAR,
    ),
    (
        Category.NgsOutfit,
        "MaleNGSOuters.csv",
        ObjectType.NGS_BODY,
        ModelPart.NGS_OUTERWEAR,
    ),
    (Category.NgsBodyPaint, "CasealNGSBodyPaint.csv", ObjectType.NGS_BODY_PAINT, None),
    (Category.NgsBodyPaint, "CastNGSBodyPaint.csv", ObjectType.NGS_BODY_PAINT, None),
    (Category.NgsBodyPaint, "FemaleNGSBodyPaint.csv", ObjectType.NGS_BODY_PAINT, None),
    (
        Category.NgsBodyPaint,
        "GenderlessNGSBodyPaint.csv",
        ObjectType.NGS_BODY_PAINT,
        None,
    ),
    (Category.NgsBodyPaint, "MaleNGSBodyPaint.csv", ObjectType.NGS_BODY_PAINT, None),
    (Category.NgsBodyPaint, "SkinsNGS.csv", ObjectType.NGS_BODY, ModelPart.NGS_SKIN),
]

_CLASSIC_PLAYER_FILES: list[FileTuple] = [
    (
        Category.ClassicHeadPart,
        "CasealFaces_Heads.csv",
        ObjectType.HEAD,
        ModelPart.FEMALE_CAST_HEAD,
    ),
    (Category.ClassicHeadPart, "CasealHair.csv", ObjectType.HAIR, None),
    (Category.ClassicHeadPart, "CastFaces_Heads.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "Eyebrows.csv", ObjectType.EYEBROW, None),
    (Category.ClassicHeadPart, "Eyelashes.csv", ObjectType.EYELASHES, None),
    (Category.ClassicHeadPart, "Eyes.csv", ObjectType.EYE, None),
    (Category.ClassicHeadPart, "FacePaint.csv", ObjectType.FACE_PAINT, None),
    (Category.ClassicHeadPart, "FaceTextures.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "FemaleDeumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "FemaleHair.csv", ObjectType.HAIR, None),
    (Category.ClassicHeadPart, "FemaleHumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "FemaleNewmanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "MaleDeumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "MaleHair.csv", ObjectType.HAIR, None),
    (Category.ClassicHeadPart, "MaleHumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicHeadPart, "MaleNewmanFaces.csv", ObjectType.HEAD, None),
    (
        Category.ClassicCastPart,
        "CasealArms.csv",
        ObjectType.BODY,
        ModelPart.FEMALE_CAST_ARMS,
    ),
    (Category.ClassicCastPart, "CasealBodies.csv", ObjectType.BODY, None),
    (Category.ClassicCastPart, "CasealLegs.csv", ObjectType.BODY, None),
    (Category.ClassicCastPart, "CastArms.csv", ObjectType.BODY, None),
    (Category.ClassicCastPart, "CastBodies.csv", ObjectType.BODY, None),
    (Category.ClassicCastPart, "CastLegs.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "FemaleBasewear.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "FemaleCostumes.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "FemaleInnerwear.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "FemaleOuters.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "MaleBasewear.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "MaleCostumes.csv", ObjectType.BODY, None),
    (Category.ClassicOutfit, "MaleOuters.csv", ObjectType.BODY, None),
    (Category.ClassicBodyPaint, "FemaleBodyPaint.csv", ObjectType.BODY_PAINT, None),
    (
        Category.ClassicBodyPaint,
        "FemaleLayeredBodyPaint.csv",
        ObjectType.BODY_PAINT,
        None,
    ),
    (Category.ClassicBodyPaint, "MaleBodyPaint.csv", ObjectType.BODY_PAINT, None),
    (
        Category.ClassicBodyPaint,
        "MaleLayeredBodyPaint.csv",
        ObjectType.BODY_PAINT,
        None,
    ),
    (Category.ClassicBodyPaint, "Skins.csv", ObjectType.NGS_BODY, ModelPart.NGS_SKIN),
    (Category.ClassicOther, "PhotonBlastCreatures.csv", None, None),
]

_COMMON_PLAYER_FILES: list[FileTuple] = [
    (
        Category.Accessory,
        "Accessories.csv",
        ObjectType.ACCESSORY,
        None,
    ),
    (
        Category.Sticker,
        "Stickers.csv",
        ObjectType.STICKER,
        None,
    ),
    (Category.NgsOther, "DarkBlasts_DrivableVehiclesNGS.csv", None, None),
    (Category.ClassicOther, "DarkBlasts_DrivableVehicles.csv", None, None),
]

_PLAYER_FILES: list[tuple[str, list[FileTuple]]] = [
    ("Player/Classic", _CLASSIC_PLAYER_FILES),
    ("Player/NGS", _NGS_PLAYER_FILES),
    ("Player", _COMMON_PLAYER_FILES),
]

_MAG_FILES: list[FileTuple] = [
    (Category.NgsMag, "MagsNGS.csv", None, None),
    (Category.ClassicMag, "Mags.csv", None, None),
]


def get_file_groups():
    for root, files in _PLAYER_FILES:
        for category, file, object_type, model_part in files:
            yield from _read_player_csv(
                category, f"{root}/{file}", object_type, model_part
            )

    for category, file, object_type, model_part in _MAG_FILES:
        yield from _read_mag_csv(category, file)


_SEARCH_PATHS = ["win32", "win32_na", "win32reboot", "win32reboot_na"]


def find_ice_file(context: bpy.types.Context, filehash: str) -> Path | None:
    pso2_data = get_preferences(context).get_pso2_data_path()

    for basedir in _SEARCH_PATHS:
        path = pso2_data / basedir / filehash
        if path.is_file():
            return path

    return None


def _read_player_csv(
    category: Category,
    file: str,
    object_type: Optional[ObjectType] = None,
    model_part: Optional[ModelPart] = None,
):
    try:
        objects: dict[int, dict[str, str]] = {}

        for row in _read_csv(file):
            try:
                yield from _parse_player_csv_row(
                    objects, category, row, object_type, model_part
                )
            except ValueError as ex:
                print(ex)
    except OSError as ex:
        print(ex)


def _read_mag_csv(
    category: Category,
    file: str,
    object_type: Optional[ObjectType] = None,
    model_part: Optional[ModelPart] = None,
):
    try:
        for row in _read_headerless_csv(f"Player/{file}"):
            try:
                yield from _parse_mag_csv_row(category, row)
            except ValueError as ex:
                print(ex)
    except OSError as ex:
        print(ex)


def _parse_player_csv_row(
    objects: dict[int, dict[str, str]],
    category: Category,
    row: dict[str, str],
    object_type: Optional[ObjectType] = None,
    model_part: Optional[ModelPart] = None,
):
    object_id = int(row.get("Id", "0"))
    objects[object_id] = row

    en_name = row.get("English Name")
    jp_name = row.get("Japanese Name")
    name = en_name or f"{jp_name} ({object_id})" if jp_name else f"Unnamed {object_id}"

    adjusted_id = int(row.get("Adjusted Id", "0"))
    base_object = objects.get(adjusted_id, {}) if adjusted_id != object_id else {}

    group = FileGroup(category, name, object_type, object_id, model_part)

    def get_file(column: str):
        return row.get(column) or base_object.get(column)

    common_files = [get_file("Material Anim"), get_file("Material Anim Ex")]

    if model := row.get("High Quality"):
        group.files[VARIANT_HIGH_QUALITY] = _filter_list(
            *common_files,
            get_file("HQ Hand Textures"),
            get_file("HQ Linked Inner"),
            model,
        )

    if model := row.get("Normal Quality"):
        group.files[VARIANT_NORMAL_QUALITY] = _filter_list(
            *common_files,
            get_file("Hand Textures"),
            get_file("Linked Inner"),
            model,
        )

    if model := row.get("Normal Quality RP"):
        group.files[VARIANT_REPLACEMENT] = _filter_list(
            *common_files,
            get_file("Hand Textures"),
            get_file("Linked Inner"),
            model,
        )

    # TODO: "High Quality RP" column exists, but nothing uses it?

    if group.files:
        yield group


def _filter_list(*files: list[str]):
    return filter(bool, files)


def _read_csv(name: str):
    path = FILE_LIST_DIR / name
    with path.open(
        newline="", encoding="utf-8-sig", errors="surrogateescape"
    ) as csvfile:
        yield from csv.DictReader(csvfile)


def _parse_mag_csv_row(
    category: Category,
    row: list[str],
):
    try:
        if row[-1] == "(Not found)":
            return

        name = row[1]
        icefile = row[3]
        group = FileGroup(category, name)
        group.files[VARIANT_NORMAL_QUALITY] = [icefile]

        yield group
    except IndexError:
        pass


def _read_headerless_csv(name: str):
    path = FILE_LIST_DIR / name
    with path.open(
        newline="", encoding="utf-8-sig", errors="surrogateescape"
    ) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            yield row
