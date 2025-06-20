import hashlib
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, fields
from enum import StrEnum
from pathlib import Path
from typing import Any, Generator, Iterable, Type, TypeVar

import bpy
import System
import System.Collections.Generic
import System.IO
from AquaModelLibrary.Data.PSO2.Aqua import CharacterMakingIndex, PSO2Text
from AquaModelLibrary.Data.PSO2.Aqua.CharacterMakingIndexData import (
    ACCEObject,
    BBLYObject,
    BCLNObject,
    BODYObject,
    EYEBObject,
    EYEObject,
    FACEObject,
    FaceTextureObject,
    FCPObject,
    HAIRObject,
    NGS_EarObject,
    NGS_HornObject,
    NGS_SKINObject,
    NGS_TeethObject,
    StickerObject,
)
from AquaModelLibrary.Data.PSO2.Constants import CharacterMakingDynamic
from AquaModelLibrary.Data.Utility import ReferenceGenerator

from . import datafile, ice, preferences
from .colors import ColorId, ColorMapping
from .debug import debug_print
from .paths import get_data_path
from .util import dict_get

T = TypeVar("T", bound="CmxObjectBase")
NameDict = defaultdict[int, list[str]]


class ObjectType(StrEnum):
    ACCESSORY = "accessory"
    BASEWEAR = "basewear"
    BODYPAINT = "bodypaint"
    CAST_ARMS = "cast_arms"
    CAST_BODY = "cast_body"
    CAST_LEGS = "cast_legs"
    COSTUME = "costume"
    EAR = "ear"
    EYE = "eye"
    EYEBROW = "eyebrow"
    EYELASH = "eyelash"
    FACE = "face"
    FACE_TEXTURE = "face_texture"
    FACEPAINT = "facepaint"
    HAIR = "hair"
    HORN = "horn"
    INNERWEAR = "innerwear"
    OUTERWEAR = "outerwear"
    SKIN = "skin"
    STICKER = "sticker"
    TEETH = "teeth"


class CmxCategory(StrEnum):
    """Category keys for CMX text dictionaries"""

    ARKS_CARD_BG = "arkscardbg"
    ARM = "arm"
    BASEWEAR = "basewear"
    BODY = "body"
    BODYPAINT1 = "bodypaint1"
    BODYPAINT2 = "bodypaint2"
    COSTUME = "costume"
    EARS = "ears"
    EYE = "eye"
    EYEBROWS = "eyebrows"
    EYELASHES = "eyelashes"
    FACE = "face"
    FACE_ANIM = "faceanim"
    FACEPAINT1 = "facepaint1"
    FACEPAINT2 = "facepaint2"
    FACE_VARIATION = "facevariation"
    HAIR = "hair"
    HORN = "horn"
    INNERWEAR = "innerwear"
    LEG = "Leg"
    MOTION = "motion"
    SKIN = "skin"
    TEETH = "dental"
    VOICE = "voice"

    ACCESSORY = "decoy"


CLASSIC_START = 0
CLASSIC_MALE_COSTUME_START = 0
CLASSIC_FEMALE_COSTUME_START = 10000
CLASSIC_MALE_START = 20000
CLASSIC_FEMALE_START = 30000
CLASSIC_CAST_START = 40000
CLASSIC_CASEAL_START = 50000
CLASSIC_UNKNOWN_START = 60000
NGS_START = 100000
NGS_T1_START = 100000
NGS_T2_START = 200000
NGS_CAST_START = 300000
NGS_CASEAL_START = 400000
NGS_GENDERLESS_START = 500000
NGS_UNKNOWN_START = 600000


def is_ngs(object_id: int):
    return object_id >= NGS_START


def is_t1(object_id: int):
    return (
        CLASSIC_MALE_COSTUME_START <= object_id < CLASSIC_FEMALE_COSTUME_START
        or CLASSIC_MALE_START <= object_id < CLASSIC_FEMALE_START
        or CLASSIC_CAST_START <= object_id < CLASSIC_CASEAL_START
        or NGS_T1_START <= object_id < NGS_T2_START
        or NGS_CAST_START <= object_id < NGS_CASEAL_START
    )


def is_t2(object_id: int):
    return (
        CLASSIC_FEMALE_COSTUME_START <= object_id < CLASSIC_MALE_START
        or CLASSIC_FEMALE_START <= object_id < CLASSIC_CAST_START
        or CLASSIC_CASEAL_START <= object_id < CLASSIC_UNKNOWN_START
        or NGS_T2_START <= object_id < NGS_CAST_START
        or NGS_CASEAL_START <= object_id < NGS_GENDERLESS_START
    )


def is_genderless(object_id: int):
    return not is_t1(object_id) and not is_t2(object_id)


def md5digest(text: str):
    """Get an MD5 hex digest of a string"""
    return hashlib.md5(text.encode()).hexdigest()


def md5digest_ex(text: str):
    """Get an MD5 hex digest of a string with '_ex' appended to it"""
    return md5digest(text + "_ex")


@dataclass
class CmxColorMapping(ColorMapping):
    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return f"{self.red};{self.green};{self.blue};{self.alpha}"
        raise NotImplementedError()

    @classmethod
    def from_body_obj(cls, obj: BODYObject):
        mapping = obj.bodyMaskColorMapping
        return cls(
            red=ColorId(int(mapping.redIndex)),
            green=ColorId(int(mapping.greenIndex)),
            blue=ColorId(int(mapping.blueIndex)),
            alpha=ColorId(int(mapping.alphaIndex)),
        )

    @classmethod
    def from_ear_obj(cls, obj: NGS_EarObject):
        return cls(
            red=ColorId(int(obj.ngsEar.unkInt1)),
            green=ColorId(int(obj.ngsEar.unkInt2)),
            blue=ColorId(int(obj.ngsEar.unkInt3)),
            alpha=ColorId(int(obj.ngsEar.unkInt4)),
        )

    @classmethod
    def from_hair_obj(cls, obj: HAIRObject):
        red, green = split_int32(obj.hair.unkInt16)
        blue, alpha = split_int32(obj.hair.unkInt17)
        return cls(
            red=ColorId(red),
            green=ColorId(green),
            blue=ColorId(blue),
            alpha=ColorId(alpha),
        )


def get_classic_color_map(object_type: ObjectType) -> ColorMapping | None:
    match object_type:
        case ObjectType.BASEWEAR | ObjectType.COSTUME:
            return ColorMapping(blue=ColorId.BASE1)

        case ObjectType.OUTERWEAR:
            return ColorMapping(blue=ColorId.OUTER1)

    return None


def split_int32(value: int):
    uvalue = System.UInt32(value)  # type: ignore
    lo = int(uvalue) & 0x0000FFFF  # type: ignore
    hi = int(uvalue) >> 16  # type: ignore
    return lo, hi


def convert_color_map(data: bytes):
    r, g, b, a = data.decode().split(";")
    return CmxColorMapping(
        red=ColorId(int(r)),
        green=ColorId(int(g)),
        blue=ColorId(int(b)),
        alpha=ColorId(int(a)),
    )


sqlite3.register_converter("COLOR_MAP", convert_color_map)


class CmxFileName:
    name: str

    def __init__(self, name: str = ""):
        self.name = name

    def __bool__(self):
        return bool(self.name)

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.name
        raise NotImplementedError()

    @property
    def hash(self):
        return md5digest(self.name)

    @property
    def ex(self):
        start: str = CharacterMakingDynamic.rebootStart
        ex: str = CharacterMakingDynamic.rebootExStart

        if not self.name.startswith(start):
            return CmxFileName()

        name = self.name.replace(start, ex).replace(".ice", "_ex.ice")
        return CmxFileName(name)

    def path(self, data_path: Path):
        if not self:
            return None

        file_hash = self.hash
        reboot_hash = file_hash[0:2] + "/" + file_hash[2:]

        paths = [
            data_path / "win32" / file_hash,
            data_path / "win32reboot" / reboot_hash,
            data_path / "win32_na" / file_hash,
            data_path / "win32reboot_na" / reboot_hash,
        ]

        return next((p for p in paths if p.exists()), None)

    def exists(self, data_path: Path):
        return self.path(data_path) is not None


def convert_file_name(data: bytes):
    return CmxFileName(data.decode())


sqlite3.register_converter("FILENAME", convert_file_name)


def _db_attr(name: str):
    if name == "id":
        return "PRIMARY KEY"
    return ""


def _db_type(cls: Type[Any] | str | Any) -> str:
    if cls == str:
        return "TEXT NOT NULL"

    if cls == int | None:
        return "INTGER"
    if cls == int:
        return "INTEGER NOT NULL"

    if cls == float | None:
        return "REAL"
    if cls == float:
        return "REAL NOT NULL"

    if cls == CmxFileName:
        return "FILENAME"

    if cls == CmxColorMapping:
        return "COLOR_MAP"

    raise NotImplementedError(f"Unhandled type {cls}")


@dataclass
class CmxObjectBase:
    object_type: ObjectType
    id: int
    adjusted_id: int
    name_en: str = ""
    name_jp: str = ""

    _NO_COLUMN = ["object_type"]

    @property
    def name(self):
        return self.name_en or self.name_jp or f"Unnamed {self.id}"

    @property
    def is_ngs(self):
        return is_ngs(self.id)

    @property
    def is_t1(self):
        return is_t1(self.id)

    @property
    def is_t2(self):
        return is_t2(self.id)

    @property
    def is_genderless(self):
        return is_genderless(self.id)

    def get_colors(self) -> set[ColorId]:
        return self.get_color_map().get_used_colors()

    def get_color_map(self) -> ColorMapping:
        return ColorMapping()

    def get_files(self) -> list[CmxFileName]:
        return [f for f in self._get_files() if f]

    def get_textures(self) -> list[str]:
        return [t for t in self._get_textures() if t]

    def _get_files(self) -> Iterable[CmxFileName]:
        return []

    def _get_textures(self) -> Iterable[str]:
        return []

    @classmethod
    def from_db_row(cls, object_type: ObjectType, row: sqlite3.Row):
        d = {k: row[k] for k in row.keys() if row[k] is not None}

        return cls(object_type=object_type, **d)

    @classmethod
    def db_schema(cls, table: ObjectType):
        columns = [
            f"{field.name} {_db_type(field.type)} {_db_attr(field.name)}"
            for field in fields(cls)
            if field.name not in cls._NO_COLUMN
        ]

        return f"CREATE TABLE {table}( {','.join(columns)} );"

    def db_insert(self, con: sqlite3.Connection):
        d = {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name not in self._NO_COLUMN
        }

        placeholders = ",".join(":" + k for k in d.keys())

        con.execute(f"INSERT INTO {self.object_type} VALUES({placeholders})", d)


@dataclass
class CmxObjectWithFile(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)

    def _get_files(self) -> Iterable[CmxFileName]:
        return [self.file]

    @classmethod
    def db_schema(cls, table: ObjectType):
        return f"""
            {super().db_schema(table)}
            CREATE INDEX {table}_file ON {table}(md5(file));
            CREATE INDEX {table}_file_ex ON {table}(md5_ex(file));
            """


_object_types: dict[ObjectType, Type[CmxObjectBase]] = {}


def register_object(*object_types: ObjectType):
    def decorator(cls):
        for typ in object_types:
            _object_types[typ] = cls
        return cls

    return decorator


@dataclass
@register_object(ObjectType.ACCESSORY)
class CmxAccessory(CmxObjectWithFile):
    pass


@dataclass
@register_object(ObjectType.BODYPAINT, ObjectType.INNERWEAR)
class CmxBodyPaint(CmxObjectWithFile):
    pass


@dataclass
@register_object(ObjectType.STICKER)
class CmxSticker(CmxObjectWithFile):
    pass


@dataclass
@register_object(ObjectType.SKIN)
class CmxSkinObject(CmxObjectWithFile):
    pass


@dataclass
@register_object(ObjectType.BASEWEAR, ObjectType.OUTERWEAR, ObjectType.COSTUME)
@register_object(ObjectType.CAST_BODY, ObjectType.CAST_ARMS, ObjectType.CAST_LEGS)
class CmxBodyObject(CmxObjectBase):
    head_id: int | None = None
    sound_id: int | None = None
    linked_inner_id: int | None = None
    linked_outer_id: int | None = None

    file: CmxFileName = field(default_factory=CmxFileName)
    linked_inner_file: CmxFileName = field(default_factory=CmxFileName)
    linked_outer_file: CmxFileName = field(default_factory=CmxFileName)
    # TODO: _rp alt model
    # TODO: classic hand textures
    # TODO: material animation (AQV)
    sound_file: CmxFileName = field(default_factory=CmxFileName)
    cast_sound_file: CmxFileName = field(default_factory=CmxFileName)

    leg_length: float | None = None
    color_mapping: CmxColorMapping = field(default_factory=CmxColorMapping)

    def get_colors(self) -> set[ColorId]:
        # TODO: currently just assuming every body part uses skin colors.
        # Is there a way to check without inspecting the .aqp file's materials?
        colors = self.get_color_map().get_used_colors()
        colors.add(ColorId.MAIN_SKIN)

        if self.is_ngs:
            colors.add(ColorId.SUB_SKIN)

        return colors

    def get_color_map(self) -> ColorMapping:
        if self.is_ngs:
            return self.color_mapping

        if classic_colors := get_classic_color_map(self.object_type):
            return classic_colors

        return self.color_mapping

    def _get_files(self) -> Iterable[CmxFileName]:
        # Ignoring sound files, as those aren't needed for import.
        return [self.file, self.linked_inner_file, self.linked_outer_file]


@dataclass
@register_object(ObjectType.FACE)
class CmxFaceObject(CmxObjectWithFile):
    def get_color_map(self) -> ColorMapping:
        return ColorMapping(red=ColorId.MAIN_SKIN, green=ColorId.SUB_SKIN)


@dataclass
@register_object(ObjectType.FACE_TEXTURE, ObjectType.FACEPAINT)
class CmxFacePaint(CmxObjectWithFile):
    pass


@dataclass
@register_object(ObjectType.EYE)
class CmxEyeObject(CmxObjectWithFile):
    def get_colors(self) -> set[ColorId]:
        return {ColorId.LEFT_EYE, ColorId.RIGHT_EYE}


@dataclass
@register_object(ObjectType.EYEBROW, ObjectType.EYELASH)
class CmxEyebrowObject(CmxObjectWithFile):
    def get_color_map(self) -> ColorMapping:
        if self.object_type == ObjectType.EYEBROW:
            return ColorMapping(red=ColorId.EYEBROW)

        return ColorMapping(red=ColorId.EYELASH)


@dataclass
@register_object(ObjectType.HAIR)
class CmxHairObject(CmxObjectWithFile):
    color_mapping: CmxColorMapping = field(default_factory=CmxColorMapping)

    def get_color_map(self) -> ColorMapping:
        return self.color_mapping


@dataclass
@register_object(ObjectType.EAR)
class CmxEarObject(CmxObjectWithFile):
    color_mapping: CmxColorMapping = field(default_factory=CmxColorMapping)

    def get_color_map(self) -> ColorMapping:
        return self.color_mapping


@dataclass
@register_object(ObjectType.TEETH)
class CmxTeethObject(CmxObjectWithFile):
    pass


@dataclass
@register_object(ObjectType.HORN)
class CmxHornObject(CmxObjectWithFile):
    pass


class ObjectDatabase:
    VERSION = 4

    def __init__(self, context: bpy.types.Context):
        self.context = context
        self.con = self._open_db()

    def close(self):
        self.con.close()

    def get_all(
        self, item_id: int | None = None, file_hash: str | None = None
    ) -> Generator[CmxObjectBase, None, None]:
        for object_type, cls in _object_types.items():
            yield from self._get_objects(cls, object_type, item_id, file_hash)

    def get_accessories(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxAccessory, ObjectType.ACCESSORY, item_id, file_hash)

    def get_basewear(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxBodyObject, ObjectType.BASEWEAR, item_id, file_hash)

    def get_bodypaint(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxBodyPaint, ObjectType.BODYPAINT, item_id, file_hash)

    def get_cast_arms(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(
            CmxBodyObject, ObjectType.CAST_ARMS, item_id, file_hash
        )

    def get_cast_bodies(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(
            CmxBodyObject, ObjectType.CAST_BODY, item_id, file_hash
        )

    def get_cast_legs(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(
            CmxBodyObject, ObjectType.CAST_LEGS, item_id, file_hash
        )

    def get_costumes(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxBodyObject, ObjectType.COSTUME, item_id, file_hash)

    def get_ears(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxEarObject, ObjectType.EAR, item_id, file_hash)

    def get_eyes(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxEyeObject, ObjectType.EYE, item_id, file_hash)

    def get_eyebrows(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(
            CmxEyebrowObject, ObjectType.EYEBROW, item_id, file_hash
        )

    def get_eyelashes(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(
            CmxEyebrowObject, ObjectType.EYELASH, item_id, file_hash
        )

    def get_faces(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxFaceObject, ObjectType.FACE, item_id, file_hash)

    def get_face_textures(
        self, item_id: int | None = None, file_hash: str | None = None
    ):
        return self._get_objects(
            CmxFacePaint, ObjectType.FACE_TEXTURE, item_id, file_hash
        )

    def get_facepaint(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxFacePaint, ObjectType.FACEPAINT, item_id, file_hash)

    def get_hair(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxHairObject, ObjectType.HAIR, item_id, file_hash)

    def get_horns(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxHornObject, ObjectType.HORN, item_id, file_hash)

    def get_innerwear(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxBodyPaint, ObjectType.INNERWEAR, item_id, file_hash)

    def get_outerwear(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(
            CmxBodyObject, ObjectType.OUTERWEAR, item_id, file_hash
        )

    def get_skins(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxSkinObject, ObjectType.SKIN, item_id, file_hash)

    def get_stickers(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxSticker, ObjectType.STICKER, item_id, file_hash)

    def get_teeth(self, item_id: int | None = None, file_hash: str | None = None):
        return self._get_objects(CmxTeethObject, ObjectType.TEETH, item_id, file_hash)

    def _get_objects(
        self,
        cls: Type[T],
        object_type: ObjectType,
        item_id: int | None = None,
        file_hash: str | None = None,
    ) -> list[T]:
        if file_hash is not None:
            q = self.con.execute(
                f"SELECT * FROM {object_type} WHERE md5(file)=? OR md5_ex(file)=?",
                (file_hash, file_hash),
            )
        elif item_id is not None:
            q = self.con.execute(f"SELECT * FROM {object_type} WHERE id=?", (item_id,))
        else:
            q = self.con.execute(f"SELECT * FROM {object_type}")

        return [cls.from_db_row(object_type, row) for row in q]

    def update_database(self):
        bin_path = preferences.get_preferences(self.context).get_pso2_bin_path()

        cmx: CharacterMakingIndex = ReferenceGenerator.ExtractCMX(str(bin_path))

        parts_text, accessory_text, common_text, common_text_reboot = (
            ReferenceGenerator.ReadCMXText(
                str(bin_path), PSO2Text(), PSO2Text(), PSO2Text(), PSO2Text()
            )
        )

        with self.con:
            self._reset_db()

            self._read_accessories(cmx, accessory_text)
            self._read_basewear(cmx, parts_text)
            self._read_bodies(cmx, parts_text)
            self._read_bodypaint(cmx, parts_text)
            self._read_cast_arms(cmx, parts_text)
            self._read_cast_legs(cmx, parts_text)
            self._read_ears(cmx, parts_text)
            self._read_eyes(cmx, parts_text)
            self._read_eyebrows(cmx, parts_text)
            self._read_eyelashes(cmx, parts_text)
            self._read_faces(cmx, parts_text, bin_path)
            self._read_face_textures(cmx, parts_text)
            self._read_facepaint(cmx, parts_text)
            self._read_hair(cmx, parts_text)
            self._read_horns(cmx, parts_text)
            self._read_innerwear(cmx, parts_text)
            self._read_outerwear(cmx, parts_text)
            self._read_skins(cmx, parts_text)
            self._read_stickers(cmx, parts_text)
            self._read_teeth(cmx, parts_text)

            # TODO: objects that aren't in CMX (enemies, weapons, etc.)

    @staticmethod
    def _open_db():
        path = get_data_path() / "objects.db"
        path.parent.mkdir(parents=True, exist_ok=True)

        con = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        con.row_factory = sqlite3.Row

        con.create_function("md5", 1, md5digest, deterministic=True)
        con.create_function("md5_ex", 1, md5digest_ex, deterministic=True)

        with con:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version == ObjectDatabase.VERSION:
                return con

            if version != 0:
                debug_print("Database version changed. Resetting.")
                con.executescript(
                    """
                    PRAGMA writable_schema = 1;
                    DELETE FROM sqlite_master where type in ('table', 'index', 'trigger');
                    PRAGMA writable_schema = 0;
                    VACUUM;
                    PRAGMA INTEGRITY_CHECK;
                    """
                )

            con.executescript(
                "".join(
                    cls.db_schema(object_type)
                    for object_type, cls in _object_types.items()
                )
            )
            con.execute(f"PRAGMA user_version={ObjectDatabase.VERSION}")

        return con

    def _reset_db(self):
        for table in ObjectType:
            self.con.execute(f"DELETE FROM {table}")

    def _read_accessories(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.ACCESSORY)
        for item_id in cmx.accessoryDict.Keys:
            obj = _get_accessory(
                ObjectType.ACCESSORY,
                cmx.accessoryDict,
                cmx.accessoryIdLink,
                names,
                item_id,
            )
            obj.db_insert(self.con)

    def _read_basewear(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.BASEWEAR)
        for item_id in cmx.baseWearDict.Keys:
            obj = _get_body(
                ObjectType.BASEWEAR,
                cmx.baseWearDict,
                cmx.baseWearIdLink,
                names,
                item_id,
            )
            obj.db_insert(self.con)

    def _read_bodies(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.COSTUME)
        names.update(_get_item_names(text, CmxCategory.BODY))

        for item_id in cmx.costumeDict.Keys:
            obj = _get_body(
                ObjectType.CAST_BODY,
                cmx.costumeDict,
                cmx.costumeIdLink,
                names,
                item_id,
            )
            if item_id < CLASSIC_CAST_START:
                obj.object_type = ObjectType.COSTUME
                obj.db_insert(self.con)
            else:
                obj.db_insert(self.con)

    def _read_bodypaint(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.BODYPAINT1)
        for item_id in cmx.bodyPaintDict.Keys:
            obj = _get_bodypaint(
                ObjectType.BODYPAINT,
                cmx.bodyPaintDict,
                None,
                names,
                item_id,
            )
            obj.db_insert(self.con)

    def _read_cast_arms(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.ARM)
        for item_id in cmx.carmDict.Keys:
            obj = _get_body(
                ObjectType.CAST_ARMS,
                cmx.carmDict,
                cmx.castArmIdLink,
                names,
                item_id,
            )
            obj.db_insert(self.con)

    def _read_cast_legs(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.LEG)
        for item_id in cmx.clegDict.Keys:
            obj = _get_body(
                ObjectType.CAST_LEGS, cmx.clegDict, cmx.clegIdLink, names, item_id
            )
            obj.db_insert(self.con)

    def _read_ears(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.EARS)
        for item_id in cmx.ngsEarDict.Keys:
            obj = _get_ear(ObjectType.EAR, cmx.ngsEarDict, names, item_id)
            obj.db_insert(self.con)

    def _read_eyes(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.EYE)
        for item_id in cmx.eyeDict.Keys:
            obj = _get_eye(ObjectType.EYE, cmx.eyeDict, names, item_id)
            obj.db_insert(self.con)

    def _read_eyebrows(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.EYEBROWS)
        for item_id in cmx.eyebrowDict.Keys:
            obj = _get_eyebrow(ObjectType.EYEBROW, cmx.eyebrowDict, names, item_id)
            obj.db_insert(self.con)

    def _read_eyelashes(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.EYELASHES)
        for item_id in cmx.eyelashDict.Keys:
            obj = _get_eyebrow(ObjectType.EYELASH, cmx.eyelashDict, names, item_id)
            obj.db_insert(self.con)

    def _read_faces(self, cmx, text, bin_path: Path):
        face_dict = _get_face_variation_dict(bin_path)

        names = _get_item_names(text, CmxCategory.FACE)
        names.update(_get_item_names(text, CmxCategory.FACE_VARIATION, face_dict))

        for item_id in cmx.faceDict.Keys:
            obj = _get_face(ObjectType.FACE, cmx.faceDict, names, item_id)
            obj.db_insert(self.con)

    def _read_face_textures(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.FACEPAINT1)
        for item_id in cmx.faceTextureDict.Keys:
            obj = _get_face_texture(
                ObjectType.FACE_TEXTURE, cmx.faceTextureDict, names, item_id
            )
            obj.db_insert(self.con)

    def _read_facepaint(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.FACEPAINT2)
        for item_id in cmx.fcpDict.Keys:
            obj = _get_facepaint(ObjectType.FACEPAINT, cmx.fcpDict, names, item_id)
            obj.db_insert(self.con)

    def _read_hair(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.HAIR)
        for item_id in cmx.hairDict.Keys:
            obj = _get_hair(ObjectType.HAIR, cmx.hairDict, names, item_id)
            obj.db_insert(self.con)

    def _read_horns(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.HORN)
        for item_id in cmx.ngsHornDict.Keys:
            obj = _get_horn(ObjectType.HORN, cmx.ngsHornDict, names, item_id)
            obj.db_insert(self.con)

    def _read_innerwear(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.INNERWEAR)
        for item_id in cmx.innerWearDict.Keys:
            obj = _get_bodypaint(
                ObjectType.INNERWEAR,
                cmx.innerWearDict,
                cmx.innerWearIdLink,
                names,
                item_id,
            )
            obj.db_insert(self.con)

    def _read_outerwear(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.COSTUME)
        for item_id in cmx.outerDict.Keys:
            obj = _get_body(
                ObjectType.OUTERWEAR, cmx.outerDict, cmx.outerWearIdLink, names, item_id
            )
            obj.db_insert(self.con)

    def _read_skins(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.SKIN)
        for item_id in cmx.ngsSkinDict.Keys:
            obj = _get_skin(ObjectType.SKIN, cmx.ngsSkinDict, names, item_id)
            obj.db_insert(self.con)

    def _read_stickers(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.BODYPAINT2)
        for item_id in cmx.stickerDict.Keys:
            obj = _get_sticker(ObjectType.STICKER, cmx.stickerDict, names, item_id)
            obj.db_insert(self.con)

    def _read_teeth(self, cmx: CharacterMakingIndex, text: PSO2Text):
        names = _get_item_names(text, CmxCategory.TEETH)
        for item_id in cmx.ngsTeethDict.Keys:
            obj = _get_teeth(ObjectType.TEETH, cmx.ngsTeethDict, names, item_id)
            obj.db_insert(self.con)


def _get_item_names(
    text, category: CmxCategory, lookup_dict: dict[str, int] | None = None
):
    result = defaultdict[int, list[str]](lambda: ["", ""])

    index = text.categoryNames.IndexOf(str(category))
    if index < 0:
        return result

    lists_by_lang = text.text[index]

    for lang, text_list in enumerate(lists_by_lang):
        for item in text_list:
            name: str = item.name

            # Name may be a key into a lookup table
            if lookup_dict:
                item_id = lookup_dict.get(name)
                if item_id is not None:
                    result[item_id][lang] = item.str
                    continue

            # Otherwise, it is "No ####"
            try:
                item_id = int(name.lower().removeprefix("no"))
                result[item_id][lang] = item.str
            except ValueError:
                debug_print(f'Failed to parse {category} ID "{item.name}"')

    return result


_N = TypeVar("_N", bound=int | float)


def _optional_number(value: _N) -> _N | None:
    return value if value >= 0 else None


def _get_adjusted_id(
    item_id: int,
    link_id_dict: "System.Collections.Generic.Dictionary_2[int, BCLNObject] | None",
):
    if link_id_dict and (link := dict_get(link_id_dict, item_id)):
        return link.bcln.fileId

    return item_id


def _get_file_path_start(item_id):
    if is_ngs(item_id):
        return CharacterMakingDynamic.rebootStart

    return CharacterMakingDynamic.classicStart


def _common_props(
    object_type: ObjectType,
    item_id: int,
    name_dict,
    link_id_dict: "System.Collections.Generic.Dictionary_2[int, BCLNObject] | None" = None,
):
    name_jp, name_en = name_dict[item_id]
    return {
        "object_type": object_type,
        "id": item_id,
        "adjusted_id": _get_adjusted_id(item_id, link_id_dict),
        "name_jp": name_jp,
        "name_en": name_en,
    }


def _get_file_tag(object_type: ObjectType):
    match object_type:
        case ObjectType.ACCESSORY:
            return "ac"
        case ObjectType.COSTUME:
            return "bd"
        case ObjectType.BASEWEAR:
            return "bw"
        case ObjectType.OUTERWEAR:
            return "ow"
        case ObjectType.CAST_ARMS:
            return "am"
        case ObjectType.CAST_BODY:
            return "bd"
        case ObjectType.CAST_LEGS:
            return "lg"
        case ObjectType.INNERWEAR:
            return "iw"
        case ObjectType.BODYPAINT:
            return "b1"
        case ObjectType.STICKER:
            return "b2"
        case ObjectType.SKIN:
            return "sk"
        case ObjectType.FACE:
            return "fc"
        case ObjectType.FACE_TEXTURE:
            return "f1"
        case ObjectType.FACEPAINT:
            return "f2"
        case ObjectType.EYE:
            return "ey"
        case ObjectType.EYEBROW:
            return "eb"
        case ObjectType.EYELASH:
            return "el"
        case ObjectType.EAR:
            return "ea"
        case ObjectType.TEETH:
            return "de"
        case ObjectType.HORN:
            return "hn"
        case ObjectType.HAIR:
            return "hr"


def _get_body(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, BODYObject]",
    link_id_dict: "System.Collections.Generic.Dictionary_2[int, BCLNObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxBodyObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.head_id = _optional_number(item.body2.headId)
        data.sound_id = _optional_number(item.body2.costumeSoundId)
        data.linked_inner_id = _optional_number(item.body2.linkedInnerId)
        data.linked_outer_id = _optional_number(item.body2.linkedOuterId)
        data.leg_length = _optional_number(item.body2.legLength)
        data.color_mapping = CmxColorMapping.from_body_obj(item)

    start = _get_file_path_start(item_id)

    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    if data.linked_inner_id is not None:
        data.linked_inner_file.name = f"{start}b1_{data.linked_inner_id:05d}.ice"

    if data.linked_outer_id is not None:
        data.linked_outer_file.name = f"{start}ow_{data.linked_outer_id:05d}.ice"

    if data.sound_id is not None:
        data.sound_file.name = f"{start}bs_{data.sound_id:05d}.ice"
        data.cast_sound_file.name = f"{start}ls_{data.sound_id:05d}.ice"

    return data


def _get_bodypaint(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, BBLYObject]",
    link_id_dict: "System.Collections.Generic.Dictionary_2[int, BCLNObject] | None",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxBodyPaint(**_common_props(object_type, item_id, name_dict, link_id_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_sticker(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, StickerObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxSticker(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_skin(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, NGS_SKINObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxSkinObject(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_face(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, FACEObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxFaceObject(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_facepaint(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, FCPObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxFacePaint(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_face_texture(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, FaceTextureObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxFacePaint(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_eye(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, EYEObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxEyeObject(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_eyebrow(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, EYEBObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxEyebrowObject(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_hair(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, HAIRObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxHairObject(**_common_props(object_type, item_id, name_dict))

    if item := dict_get(object_dict, item_id):
        if data.is_ngs:
            data.color_mapping = CmxColorMapping.from_hair_obj(item)

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_ear(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, NGS_EarObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxEarObject(**_common_props(object_type, item_id, name_dict))

    if item := dict_get(object_dict, item_id):
        data.color_mapping = CmxColorMapping.from_ear_obj(item)

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_teeth(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, NGS_TeethObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxTeethObject(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_horn(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, NGS_HornObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxHornObject(**_common_props(object_type, item_id, name_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_accessory(
    object_type: ObjectType,
    object_dict: "System.Collections.Generic.Dictionary_2[int, ACCEObject]",
    link_id_dict: "System.Collections.Generic.Dictionary_2[int, BCLNObject]",
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxAccessory(**_common_props(object_type, item_id, name_dict, link_id_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_face_variation_dict(bin_path: Path) -> dict[str, int]:
    face_var_path = bin_path / "data/win32" / md5digest("ui_character_making.ice")
    result: dict[str, int] = {}

    try:
        icefile = ice.IceFile.load(face_var_path)

        for f in icefile.get_files():
            if "face_variation.cmp.lua" in f.name.lower():
                result.update(_parse_face_variation_lua(f))
    except System.IO.FileNotFoundException:  # type: ignore
        pass

    return result


def _parse_face_variation_lua(script_file: datafile.DataFile) -> dict[str, int]:
    result: dict[str, int] = {}
    language: str | None = None
    src = script_file.data.rstrip(b"\0").decode()

    for line in src.splitlines():
        if language:
            if "crop_name" in line:
                if name := line.split('"')[1]:
                    result[language] = int(name[7:])

                language = None

        elif "language" in line:
            language = line.split('"')[1]

    return result
