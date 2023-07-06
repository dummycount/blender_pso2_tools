from collections import defaultdict
import csv
from dataclasses import dataclass, field
from pathlib import Path
import shutil
from subprocess import CalledProcessError
from typing import Optional

from .object_info import ModelPart, ObjectType

try:
    from enum import StrEnum
except ImportError:
    from .strenum import StrEnum

import bpy

from .convert import make_file_lists
from .preferences import get_preferences

DATA_DIR = Path(__file__).parent / "data"
FILE_LIST_DIR = DATA_DIR / "FileLists"


class Category(StrEnum):
    NgsOutfit = "NGS_OUTFIT"
    NgsCastPart = "NGS_CAST"
    NgsFacePart = "NGS_FACE"
    NgsBodyPaint = "NGS_PAINT"
    NgsMag = "NGS_MAG"
    NgsOther = "NGS_OTHER"

    ClassicOutfit = "CLASSIC_OUTFIT"
    ClassicCastPart = "CLASSIC_CAST"
    ClassicFacePart = "CLASSIC_FACE"
    ClassicBodyPaint = "CLASSIC_PAINT"
    ClassicMag = "CLASSIC_MAG"
    ClassicOther = "CLASSIC_OTHER"

    Accessory = "ACCESSORY"
    Room = "ROOM"
    MySpace = "MY_SPACE"

    NgsEnemies = "NGS_ENEMY"
    ClassicEnemies = "CLASSIC_ENEMY"

    # TODO: add motions


ALL_CATEGORIES = set(str(value) for value in Category)

VARIANT_HIGH_QUALITY = "High Quality"
VARIANT_NORMAL_QUALITY = "Normal Quality"
VARIANT_REPLACEMENT = "Replacement"


@dataclass
class FileGroup:
    category: Category
    name: str
    object_type: Optional[ObjectType] = None
    object_id: int = (0,)
    part: Optional[ModelPart] = None
    files: defaultdict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    @property
    def variants(self):
        return list(self.files.keys())


def update_file_lists(operator: bpy.types.Operator, context: bpy.types.Context):
    shutil.rmtree(FILE_LIST_DIR, ignore_errors=True)

    try:
        pso2_bin = Path(get_preferences(context).pso2_data_path).parent
        make_file_lists(pso2_bin, FILE_LIST_DIR)
        return {"FINISHED"}
    except CalledProcessError as ex:
        operator.report({"ERROR"}, f"Failed to update file lists:\n{ex.stderr}")
        return {"CANCELLED"}


FileTuple = tuple[Category, str, ObjectType | None, ModelPart | None]

_NGS_PLAYER_FILES: list[FileTuple] = [
    (Category.NgsFacePart, "AllFacesNGS.csv", ObjectType.NGS_HEAD, None),
    (Category.NgsFacePart, "AllHairNGS.csv", ObjectType.NGS_HAIR, None),
    (Category.NgsFacePart, "EarsNGS.csv", ObjectType.NGS_EAR, None),
    (Category.NgsFacePart, "EyebrowsNVS.csv", ObjectType.NGS_EYEBROW, None),
    (Category.NgsFacePart, "EyelashesNGS.csv", ObjectType.NGS_EYELASHES, None),
    (Category.NgsFacePart, "EyesNGS.csv", ObjectType.NGS_EYE, None),
    (Category.NgsFacePart, "FacePaintNGS.csv", ObjectType.NGS_FACE_PAINT, None),
    (Category.NgsFacePart, "HornsNGS.csv", ObjectType.NGS_HORN, None),
    (Category.NgsFacePart, "TeethNGS.csv", ObjectType.NGS_TEETH, None),
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
    (Category.NgsBodyPaint, "Skins.csv", ObjectType.NGS_BODY, ModelPart.NGS_SKIN),
]

_CLASSIC_PLAYER_FILES: list[FileTuple] = [
    (
        Category.ClassicFacePart,
        "CasealFaces_Heads.csv",
        ObjectType.HEAD,
        ModelPart.FEMALE_CAST_HEAD,
    ),
    (Category.ClassicFacePart, "CasealHair.csv", ObjectType.HAIR, None),
    (Category.ClassicFacePart, "CastFaces_Heads.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "Eyebrows.csv", ObjectType.EYEBROW, None),
    (Category.ClassicFacePart, "Eyelashes.csv", ObjectType.EYELASHES, None),
    (Category.ClassicFacePart, "Eyes.csv", ObjectType.EYE, None),
    (Category.ClassicFacePart, "FacePaint.csv", ObjectType.FACE_PAINT, None),
    (Category.ClassicFacePart, "FaceTextures.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "FemaleDeumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "FemaleHair.csv", ObjectType.HAIR, None),
    (Category.ClassicFacePart, "FemaleHumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "FemaleNewmanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "MaleDeumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "MaleHair.csv", ObjectType.HAIR, None),
    (Category.ClassicFacePart, "MaleHumanFaces.csv", ObjectType.HEAD, None),
    (Category.ClassicFacePart, "MaleNewmanFaces.csv", ObjectType.HEAD, None),
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

_COMMON_PLAYER_FILES: list[tuple[Category, str]] = [
    (Category.Accessory, "Accessories.csv"),
    (Category.NgsOther, "DarkBlasts_DrivableVehiclesNGS.csv"),
    (Category.ClassicOther, "DarkBlasts_DrivableVehicles.csv"),
    (Category.NgsMag, "MagsNGS.csv"),
    (Category.ClassicMag, "Mags.csv"),
]


def get_file_groups():
    for category, file, object_type, model_part in _NGS_PLAYER_FILES:
        yield from _read_player_csv(
            category, f"Player/NGS/{file}", object_type, model_part
        )

    for category, file, object_type, model_part in _CLASSIC_PLAYER_FILES:
        yield from _read_player_csv(
            category, f"Player/Classic/{file}", object_type, model_part
        )


_SEARCH_PATHS = ["win32", "win32_na", "win32reboot", "win32reboot_na"]


def find_ice_file(context: bpy.types.Context, filehash: str) -> Path | None:
    pso2_data = Path(get_preferences(context).pso2_data_path)

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
        for row in _read_csv(file):
            yield from _parse_player_csv_row(category, row, object_type, model_part)
    except OSError:
        pass


def _parse_player_csv_row(
    category: Category,
    row: dict[str, str],
    object_type: Optional[ObjectType] = None,
    model_part: Optional[ModelPart] = None,
):
    name = (
        row.get("English Name")
        or row.get("Japanese Name")
        or f"Unnamed {row.get('Id')}"
    )

    object_id = int(row.get("Id", "0"))
    group = FileGroup(category, name, object_type, object_id, model_part)

    common_files = [row.get("Material Anim"), row.get("Material Anim Ex")]

    if model := row.get("High Quality"):
        group.files[VARIANT_HIGH_QUALITY] = _filter_list(
            *common_files,
            row.get("HQ Hand Textures"),
            row.get("HQ Linked Inner"),
            model,
        )

    if model := row.get("Normal Quality"):
        group.files[VARIANT_NORMAL_QUALITY] = _filter_list(
            *common_files,
            row.get("Hand Textures"),
            row.get("Linked Inner"),
            model,
        )

    if model := row.get("Normal Quality RP"):
        group.files[VARIANT_REPLACEMENT] = _filter_list(
            *common_files,
            row.get("Hand Textures"),
            row.get("Linked Inner"),
            model,
        )

    # TODO: "High Quality RP" column exists, but nothing uses it?

    yield group


def _filter_list(*files: list[str]):
    return filter(bool, files)


def _read_csv(name: str):
    path = FILE_LIST_DIR / name
    with path.open(
        newline="", encoding="utf-8-sig", errors="surrogateescape"
    ) as csvfile:
        yield from csv.DictReader(csvfile)
