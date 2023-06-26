from collections import defaultdict
import csv
from dataclasses import dataclass, field
from pathlib import Path
import shutil
from subprocess import CalledProcessError

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


_NGS_PLAYER_FILES: list[tuple[Category, str]] = [
    (Category.NgsFacePart, "AllFacesNGS.csv"),
    (Category.NgsFacePart, "AllHairNGS.csv"),
    (Category.NgsFacePart, "EarsNGS.csv"),
    (Category.NgsFacePart, "EyebrowsNVS.csv"),
    (Category.NgsFacePart, "EyelashesNGS.csv"),
    (Category.NgsFacePart, "EyesNGS.csv"),
    (Category.NgsFacePart, "FacePaintNGS.csv"),
    (Category.NgsFacePart, "HornsNGS.csv"),
    (Category.NgsFacePart, "TeethNGS.csv"),
    (Category.NgsCastPart, "CasealArmsNGS.csv"),
    (Category.NgsCastPart, "CasealLegsNGS.csv"),
    (Category.NgsCastPart, "CasealNGSBodies.csv"),
    (Category.NgsCastPart, "CastArmsNGS.csv"),
    (Category.NgsCastPart, "CastLegsNGS.csv"),
    (Category.NgsCastPart, "CastBodies.csv"),
    (Category.NgsOutfit, "FemaleNGSBasewear.csv"),
    (Category.NgsOutfit, "FemaleNGSInnerwear.csv"),
    (Category.NgsOutfit, "FemaleNGSOuters.csv"),
    (Category.NgsOutfit, "GenderlessNGSBasewear.csv"),
    (Category.NgsOutfit, "MaleNGSBasewear.csv"),
    (Category.NgsOutfit, "MaleNGSInnerwear.csv"),
    (Category.NgsOutfit, "MaleNGSOuters.csv"),
    (Category.NgsBodyPaint, "CasealNGSBodyPaint.csv"),
    (Category.NgsBodyPaint, "CastNGSBodyPaint.csv"),
    (Category.NgsBodyPaint, "FemaleNGSBodyPaint.csv"),
    (Category.NgsBodyPaint, "GenderlessNGSBodyPaint.csv"),
    (Category.NgsBodyPaint, "MaleNGSBodyPaint.csv"),
    (Category.NgsBodyPaint, "Skins.csv"),
]

_CLASSIC_PLAYER_FILES: list[tuple[Category, str]] = [
    (Category.ClassicFacePart, "CasealFaces_Heads.csv"),
    (Category.ClassicFacePart, "CasealHair.csv"),
    (Category.ClassicFacePart, "CastFaces_Heads.csv"),
    (Category.ClassicFacePart, "Eyebrows.csv"),
    (Category.ClassicFacePart, "Eyelashes.csv"),
    (Category.ClassicFacePart, "Eyes.csv"),
    (Category.ClassicFacePart, "FacePaint.csv"),
    (Category.ClassicFacePart, "FaceTextures.csv"),
    (Category.ClassicFacePart, "FemaleDeumanFaces.csv"),
    (Category.ClassicFacePart, "FemaleHair.csv"),
    (Category.ClassicFacePart, "FemaleHumanFaces.csv"),
    (Category.ClassicFacePart, "FemaleNewmanFaces.csv"),
    (Category.ClassicFacePart, "MaleDeumanFaces.csv"),
    (Category.ClassicFacePart, "MaleHair.csv"),
    (Category.ClassicFacePart, "MaleHumanFaces.csv"),
    (Category.ClassicFacePart, "MaleNewmanFaces.csv"),
    (Category.ClassicCastPart, "CasealArms.csv"),
    (Category.ClassicCastPart, "CasealBodies.csv"),
    (Category.ClassicCastPart, "CasealLegs.csv"),
    (Category.ClassicCastPart, "CastArms.csv"),
    (Category.ClassicCastPart, "CastBodies.csv"),
    (Category.ClassicCastPart, "CastLegs.csv"),
    (Category.ClassicOutfit, "FemaleBasewear.csv"),
    (Category.ClassicOutfit, "FemaleCostumes.csv"),
    (Category.ClassicOutfit, "FemaleInnerwear.csv"),
    (Category.ClassicOutfit, "FemaleOuters.csv"),
    (Category.ClassicOutfit, "MaleBasewear.csv"),
    (Category.ClassicOutfit, "MaleCostumes.csv"),
    (Category.ClassicOutfit, "MaleOuters.csv"),
    (Category.ClassicBodyPaint, "FemaleBodyPaint.csv"),
    (Category.ClassicBodyPaint, "FemaleLayeredBodyPaint.csv"),
    (Category.ClassicBodyPaint, "MaleBodyPaint.csv"),
    (Category.ClassicBodyPaint, "MaleLayeredBodyPaint.csv"),
    (Category.ClassicBodyPaint, "Skins.csv"),
    (Category.ClassicOther, "PhotonBlastCreatures.csv"),
]

_COMMON_PLAYER_FILES: list[tuple[Category, str]] = [
    (Category.Accessory, "Accessories.csv"),
    (Category.NgsOther, "DarkBlasts_DrivableVehiclesNGS.csv"),
    (Category.ClassicOther, "DarkBlasts_DrivableVehicles.csv"),
    (Category.NgsMag, "MagsNGS.csv"),
    (Category.ClassicMag, "Mags.csv"),
]


def get_file_groups():
    for category, file in _NGS_PLAYER_FILES:
        yield from _read_player_csv(category, f"Player/NGS/{file}")

    for category, file in _CLASSIC_PLAYER_FILES:
        yield from _read_player_csv(category, f"Player/Classic/{file}")


_SEARCH_PATHS = ["win32", "win32_na", "win32reboot", "win32reboot_na"]


def find_ice_file(context: bpy.types.Context, filehash: str) -> Path | None:
    pso2_data = Path(get_preferences(context).pso2_data_path)

    for basedir in _SEARCH_PATHS:
        path = pso2_data / basedir / filehash
        if path.is_file():
            return path

    return None


def _read_player_csv(category: Category, file: str):
    try:
        for row in _read_csv(file):
            yield from _parse_player_csv_row(category, row)
    except OSError:
        pass


def _parse_player_csv_row(category: Category, row: dict[str, str]):
    name = row.get("English Name") or row.get("Japanese Name")
    if not name:
        return

    group = FileGroup(category, name)

    common_files = [row.get("Material Anim"), row.get("Material Anim Ex")]

    if files := _filter_list(
        *common_files,
        row.get("HQ Hand Textures"),
        row.get("HQ Linked Inner"),
        row.get("High Quality"),
    ):
        group.files[VARIANT_HIGH_QUALITY] = files

    if files := _filter_list(
        *common_files,
        row.get("Hand Textures"),
        row.get("Linked Inner"),
        row.get("Normal Quality"),
    ):
        group.files[VARIANT_NORMAL_QUALITY] = files

    if replacement := row.get("Normal Quality RP"):
        group.files[VARIANT_REPLACEMENT] = _filter_list(
            *common_files,
            row.get("Hand Textures"),
            row.get("Linked Inner"),
            replacement,
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
