import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, fields
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Generator, Optional, Type, TypeVar

import bpy
from AquaModelLibrary.Data.PSO2.Aqua import PSO2Text
from AquaModelLibrary.Data.PSO2.Constants import CharacterMakingDynamic
from AquaModelLibrary.Data.Utility import ReferenceGenerator
from AquaModelLibrary.Helpers import HashHelpers

from . import preferences
from .colors import ColorId
from .paths import get_data_path
from .util import dict_get

T = TypeVar("T")
NameDict = dict[int, list[str]]


def is_ngs(object_id):
    return object_id >= 100000


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


class CmxPartType(Enum):
    UNKNOWN = auto()
    CLASSIC_GENDERLESS = auto()
    CLASSIC_MALE = auto()
    CLASSIC_FEMALE = auto()
    CLASSIC_CAST = auto()
    CLASSIC_CASEAL = auto()
    NGS_MALE = auto()
    NGS_FEMALE = auto()
    NGS_CAST = auto()
    NGS_CASEAL = auto()
    NGS_GENDERLESS = auto()

    @staticmethod
    def from_id(part_id: int):
        if part_id < 20000:
            return CmxPartType.CLASSIC_GENDERLESS
        if part_id < 30000:
            return CmxPartType.CLASSIC_MALE
        if part_id < 40000:
            return CmxPartType.CLASSIC_FEMALE
        if part_id < 50000:
            return CmxPartType.CLASSIC_CAST
        if part_id < 60000:
            return CmxPartType.CLASSIC_CASEAL
        if part_id < 100000:
            return CmxPartType.UNKNOWN
        if part_id < 200000:
            return CmxPartType.NGS_MALE
        if part_id < 300000:
            return CmxPartType.NGS_FEMALE
        if part_id < 400000:
            return CmxPartType.NGS_CAST
        if part_id < 500000:
            return CmxPartType.NGS_CASEAL
        if part_id < 600000:
            return CmxPartType.NGS_GENDERLESS
        return CmxPartType.UNKNOWN


@dataclass
class CmxColorMapping:
    red: ColorId = ColorId.UNUSED
    green: ColorId = ColorId.UNUSED
    blue: ColorId = ColorId.UNUSED
    alpha: ColorId = ColorId.UNUSED

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return f"{self.red};{self.green};{self.blue};{self.alpha}"
        raise NotImplementedError()

    def get_colors(self) -> set[ColorId]:
        return {
            c
            for c in (self.red, self.green, self.blue, self.alpha)
            if c != ColorId.UNUSED
        }

    @classmethod
    def from_body_obj(cls, obj):
        return cls(
            red=ColorId(int(obj.redIndex)),
            green=ColorId(int(obj.greenIndex)),
            blue=ColorId(int(obj.blueIndex)),
            alpha=ColorId(int(obj.alphaIndex)),
        )


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
        return HashHelpers.GetFileHash(self.name)

    @property
    def ex(self):
        start: str = CharacterMakingDynamic.rebootStart
        ex: str = CharacterMakingDynamic.rebootExStart

        if not self.name.startswith(start):
            return CmxFileName()

        name = self.name.replace(start, ex).replace(".ice", "_ex.ice")
        return CmxFileName(name)

    def path(self, data_path: Path):
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


def _db_type(cls: Type):
    if cls == str:
        return "TEXT NOT NULL"

    if cls == Optional[int]:
        return "INTGER"
    if cls == int:
        return "INTEGER NOT NULL"

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

    _NO_COLUMN = "object_type"

    @property
    def name(self):
        return self.name_en or self.name_jp or f"Unnamed {self.id}"

    @property
    def type(self):
        return CmxPartType.from_id(self.id)

    def get_colors(self) -> set[ColorId]:
        return set()

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
class CmxAccessory(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    node_attach_1: str = ""
    node_attach_2: str = ""
    node_attach_3: str = ""
    node_attach_4: str = ""
    node_attach_5: str = ""
    node_attach_6: str = ""
    node_attach_7: str = ""
    node_attach_8: str = ""
    node_attach_9: str = ""
    node_attach_10: str = ""
    node_attach_11: str = ""
    node_attach_12: str = ""
    node_attach_13: str = ""
    node_attach_14: str = ""
    node_attach_15: str = ""
    node_attach_16: str = ""
    node_attach_17: str = ""
    node_attach_18: str = ""
    effect_name: str = ""


@dataclass
class CmxBodyPaint(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""


@dataclass
class CmxSticker(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex: str = ""


@dataclass
class CmxSkinObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""
    tex_6: str = ""
    tex_7: str = ""
    tex_8: str = ""
    tex_9: str = ""
    tex_10: str = ""


@dataclass
class CmxBodyObject(CmxObjectBase):
    head_id: Optional[int] = None
    sound_id: Optional[int] = None
    linked_inner_id: Optional[int] = None
    linked_outer_id: Optional[int] = None

    file: CmxFileName = field(default_factory=CmxFileName)
    linked_inner_file: CmxFileName = field(default_factory=CmxFileName)
    linked_outer_file: CmxFileName = field(default_factory=CmxFileName)
    # TODO: _rp alt model
    # TODO: classic hand textures
    # TODO: material animation (AQV)
    sound_file: CmxFileName = field(default_factory=CmxFileName)
    cast_sound_file: CmxFileName = field(default_factory=CmxFileName)

    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""
    tex_6: str = ""
    leg_length: float = 0
    color_mapping: CmxColorMapping = field(default_factory=CmxColorMapping)

    def get_colors(self) -> set[ColorId]:
        # TODO: currently just assuming every body part uses skin colors.
        # Is there a way to check without inspecting the .aqp file's materials?
        colors = {ColorId.MAIN_SKIN, ColorId.SUB_SKIN}
        colors |= self.color_mapping.get_colors()
        return colors


@dataclass
class CmxFaceObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""
    tex_6: str = ""

    def get_colors(self) -> set[ColorId]:
        return {ColorId.MAIN_SKIN, ColorId.SUB_SKIN}


@dataclass
class CmxFacePaint(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""


@dataclass
class CmxEyeObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""

    def get_colors(self) -> set[ColorId]:
        return {ColorId.LEFT_EYE, ColorId.RIGHT_EYE}


@dataclass
class CmxEyebrowObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""

    def get_colors(self) -> set[ColorId]:
        if self.object_type == ObjectType.EYEBROW:
            return {ColorId.EYEBROW}
        return {ColorId.EYELASH}


@dataclass
class CmxHairObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""
    tex_6: str = ""
    tex_7: str = ""

    def get_colors(self) -> set[ColorId]:
        return {ColorId.HAIR1, ColorId.HAIR2}


@dataclass
class CmxEarObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""

    def get_colors(self) -> set[ColorId]:
        return {ColorId.MAIN_SKIN, ColorId.SUB_SKIN}


@dataclass
class CmxTeethObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""


@dataclass
class CmxHornObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)


class ObjectDatabase:
    def __init__(self, context: bpy.types.Context):
        self.context = context
        self.con = self._open_db()

    def close(self):
        self.con.close()

    def get_all(self) -> Generator[CmxObjectBase, None, None]:
        yield from self.get_accessories()
        yield from self.get_costumes()
        yield from self.get_basewear()
        yield from self.get_outerwear()
        yield from self.get_cast_arms()
        yield from self.get_cast_bodies()
        yield from self.get_cast_legs()
        yield from self.get_innerwear()
        yield from self.get_bodypaint()
        yield from self.get_stickers()
        yield from self.get_skins()
        yield from self.get_faces()
        yield from self.get_face_textures()
        yield from self.get_eyes()
        yield from self.get_eyebrows()
        yield from self.get_eyelashes()
        yield from self.get_ears()
        yield from self.get_teeth()
        yield from self.get_horns()
        yield from self.get_hair()

    def get_accessories(self, item_id: Optional[int] = None):
        return self._get_objects(CmxAccessory, ObjectType.ACCESSORY, item_id)

    def get_costumes(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, ObjectType.COSTUME, item_id)

    def get_basewear(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, ObjectType.BASEWEAR, item_id)

    def get_outerwear(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, ObjectType.OUTERWEAR, item_id)

    def get_cast_arms(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, ObjectType.CAST_ARMS, item_id)

    def get_cast_bodies(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, ObjectType.CAST_BODY, item_id)

    def get_cast_legs(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, ObjectType.CAST_LEGS, item_id)

    def get_innerwear(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyPaint, ObjectType.INNERWEAR, item_id)

    def get_bodypaint(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyPaint, ObjectType.BODYPAINT, item_id)

    def get_stickers(self, item_id: Optional[int] = None):
        return self._get_objects(CmxSticker, ObjectType.STICKER, item_id)

    def get_skins(self, item_id: Optional[int] = None):
        return self._get_objects(CmxSkinObject, ObjectType.SKIN, item_id)

    def get_faces(self, item_id: Optional[int] = None):
        return self._get_objects(CmxFaceObject, ObjectType.FACE, item_id)

    def get_face_textures(self, item_id: Optional[int] = None):
        return self._get_objects(CmxFacePaint, ObjectType.FACE_TEXTURE, item_id)

    def get_facepaint(self, item_id: Optional[int] = None):
        return self._get_objects(CmxFacePaint, ObjectType.FACEPAINT, item_id)

    def get_eyes(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEyeObject, ObjectType.EYE, item_id)

    def get_eyebrows(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEyebrowObject, ObjectType.EYEBROW, item_id)

    def get_eyelashes(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEyebrowObject, ObjectType.EYELASH, item_id)

    def get_ears(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEarObject, ObjectType.EAR, item_id)

    def get_teeth(self, item_id: Optional[int] = None):
        return self._get_objects(CmxTeethObject, ObjectType.TEETH, item_id)

    def get_horns(self, item_id: Optional[int] = None):
        return self._get_objects(CmxHornObject, ObjectType.HORN, item_id)

    def get_hair(self, item_id: Optional[int] = None):
        return self._get_objects(CmxHairObject, ObjectType.HAIR, item_id)

    def _get_objects(
        self, cls: Type[T], object_type: ObjectType, item_id: Optional[int] = None
    ) -> list[T]:
        if item_id is not None:
            q = self.con.execute(f"SELECT * FROM {object_type} WHERE id=?", (item_id,))
        else:
            q = self.con.execute(f"SELECT * FROM {object_type}")

        return [cls.from_db_row(object_type, row) for row in q]

    def update_database(self):
        bin_path = preferences.get_preferences(self.context).get_pso2_bin_path()

        cmx = ReferenceGenerator.ExtractCMX(str(bin_path))

        parts_text, accessory_text, common_text, common_text_reboot = (
            ReferenceGenerator.ReadCMXText(
                str(bin_path), PSO2Text(), PSO2Text(), PSO2Text(), PSO2Text()
            )
        )

        with self.con:
            self._reset_db()

            self._read_accessories(cmx, accessory_text)
            self._read_bodies(cmx, parts_text)
            self._read_basewear(cmx, parts_text)
            self._read_outerwear(cmx, parts_text)
            self._read_cast_arms(cmx, parts_text)
            self._read_cast_legs(cmx, parts_text)
            self._read_innerwear(cmx, parts_text)
            self._read_bodypaint(cmx, parts_text)
            self._read_stickers(cmx, parts_text)
            self._read_skins(cmx, parts_text)
            self._read_faces(cmx, parts_text)
            self._read_face_textures(cmx, parts_text)
            self._read_facepaint(cmx, parts_text)
            self._read_eyes(cmx, parts_text)
            self._read_eyebrows(cmx, parts_text)
            self._read_eyelashes(cmx, parts_text)
            self._read_ears(cmx, parts_text)
            self._read_teeth(cmx, parts_text)
            self._read_horns(cmx, parts_text)
            self._read_hair(cmx, parts_text)

            # TODO: objects that aren't in CMX (enemies, weapons, etc.)

    @staticmethod
    def _open_db():
        path = get_data_path() / "objects.db"
        path.parent.mkdir(parents=True, exist_ok=True)

        con = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        con.row_factory = sqlite3.Row

        with con:
            version = con.execute("PRAGMA user_version").fetchone()[0]

            if version < 1:
                con.executescript(
                    f"""
                    {CmxAccessory.db_schema(ObjectType.ACCESSORY)}
                    {CmxBodyObject.db_schema(ObjectType.COSTUME)}
                    {CmxBodyObject.db_schema(ObjectType.BASEWEAR)}
                    {CmxBodyObject.db_schema(ObjectType.OUTERWEAR)}
                    {CmxBodyObject.db_schema(ObjectType.CAST_BODY)}
                    {CmxBodyObject.db_schema(ObjectType.CAST_ARMS)}
                    {CmxBodyObject.db_schema(ObjectType.CAST_LEGS)}
                    {CmxBodyPaint.db_schema(ObjectType.INNERWEAR)}
                    {CmxBodyPaint.db_schema(ObjectType.BODYPAINT)}
                    {CmxSticker.db_schema(ObjectType.STICKER)}
                    {CmxSkinObject.db_schema(ObjectType.SKIN)}
                    {CmxFaceObject.db_schema(ObjectType.FACE)}
                    {CmxFacePaint.db_schema(ObjectType.FACE_TEXTURE)}
                    {CmxFacePaint.db_schema(ObjectType.FACEPAINT)}
                    {CmxEyeObject.db_schema(ObjectType.EYE)}
                    {CmxEyebrowObject.db_schema(ObjectType.EYEBROW)}
                    {CmxEyebrowObject.db_schema(ObjectType.EYELASH)}
                    {CmxEarObject.db_schema(ObjectType.EAR)}
                    {CmxTeethObject.db_schema(ObjectType.TEETH)}
                    {CmxHornObject.db_schema(ObjectType.HORN)}
                    {CmxHairObject.db_schema(ObjectType.HAIR)}
                    """
                )
                con.execute("PRAGMA user_version=1")

        return con

    def _reset_db(self):
        for table in ObjectType:
            self.con.execute(f"DELETE FROM {table}")

    def _read_accessories(self, cmx, text):
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

    def _read_cast_arms(self, cmx, text):
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

    def _read_cast_legs(self, cmx, text):
        names = _get_item_names(text, CmxCategory.LEG)
        for item_id in cmx.clegDict.Keys:
            obj = _get_body(
                ObjectType.CAST_LEGS, cmx.clegDict, cmx.clegIdLink, names, item_id
            )
            obj.db_insert(self.con)

    def _read_bodies(self, cmx, text):
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
            if item_id < 40000:
                obj.object_type = ObjectType.COSTUME
                obj.db_insert(self.con)
            else:
                obj.db_insert(self.con)

    def _read_basewear(self, cmx, text):
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

    def _read_outerwear(self, cmx, text):
        names = _get_item_names(text, CmxCategory.COSTUME)
        for item_id in cmx.outerDict.Keys:
            obj = _get_body(
                ObjectType.OUTERWEAR, cmx.outerDict, cmx.outerWearIdLink, names, item_id
            )
            obj.db_insert(self.con)

    def _read_innerwear(self, cmx, text):
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

    def _read_bodypaint(self, cmx, text):
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

    def _read_stickers(self, cmx, text):
        names = _get_item_names(text, CmxCategory.BODYPAINT2)
        for item_id in cmx.stickerDict.Keys:
            obj = _get_sticker(
                ObjectType.STICKER, cmx.stickerDict, None, names, item_id
            )
            obj.db_insert(self.con)

    def _read_skins(self, cmx, text):
        names = _get_item_names(text, CmxCategory.SKIN)
        for item_id in cmx.ngsSkinDict.Keys:
            obj = _get_skin(ObjectType.SKIN, cmx.ngsSkinDict, None, names, item_id)
            obj.db_insert(self.con)

    def _read_faces(self, cmx, text):
        names = _get_item_names(text, CmxCategory.FACE)
        # TODO: need to parse face_variation.cmp.lua in 75b1632526cd6a1039625349df6ee8dd
        # names.update(_get_item_names(text, CmxCategory.FACE_VARIATION))

        for item_id in cmx.faceDict.Keys:
            obj = _get_face(ObjectType.FACE, cmx.faceDict, None, names, item_id)
            obj.db_insert(self.con)

    def _read_face_textures(self, cmx, text):
        names = _get_item_names(text, CmxCategory.FACEPAINT1)
        for item_id in cmx.faceTextureDict.Keys:
            obj = _get_facepaint(
                ObjectType.FACE_TEXTURE, cmx.faceTextureDict, None, names, item_id
            )
            obj.db_insert(self.con)

    def _read_facepaint(self, cmx, text):
        names = _get_item_names(text, CmxCategory.FACEPAINT2)
        for item_id in cmx.fcpDict.Keys:
            obj = _get_facepaint(
                ObjectType.FACEPAINT, cmx.fcpDict, None, names, item_id
            )
            obj.db_insert(self.con)

    def _read_eyes(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EYE)
        for item_id in cmx.eyeDict.Keys:
            obj = _get_eye(ObjectType.EYE, cmx.eyeDict, None, names, item_id)
            obj.db_insert(self.con)

    def _read_eyebrows(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EYEBROWS)
        for item_id in cmx.eyebrowDict.Keys:
            obj = _get_eyebrow(
                ObjectType.EYEBROW, cmx.eyebrowDict, None, names, item_id
            )
            obj.db_insert(self.con)

    def _read_eyelashes(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EYELASHES)
        for item_id in cmx.eyelashDict.Keys:
            obj = _get_eyebrow(
                ObjectType.EYELASH, cmx.eyelashDict, None, names, item_id
            )
            obj.db_insert(self.con)

    def _read_hair(self, cmx, text):
        names = _get_item_names(text, CmxCategory.HAIR)
        for item_id in cmx.hairDict.Keys:
            obj = _get_hair(ObjectType.HAIR, cmx.hairDict, None, names, item_id)
            obj.db_insert(self.con)

    def _read_ears(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EARS)
        for item_id in cmx.ngsEarDict.Keys:
            obj = _get_ear(ObjectType.EAR, cmx.ngsEarDict, None, names, item_id)
            obj.db_insert(self.con)

    def _read_teeth(self, cmx, text):
        names = _get_item_names(text, CmxCategory.TEETH)
        for item_id in cmx.ngsTeethDict.Keys:
            obj = _get_teeth(ObjectType.TEETH, cmx.ngsTeethDict, None, names, item_id)
            obj.db_insert(self.con)

    def _read_horns(self, cmx, text):
        names = _get_item_names(text, CmxCategory.HORN)
        for item_id in cmx.ngsHornDict.Keys:
            obj = _get_horn(ObjectType.HORN, cmx.ngsHornDict, None, names, item_id)
            obj.db_insert(self.con)


def _get_item_names(text, category: CmxCategory):
    index = text.categoryNames.IndexOf(str(category))
    if index < 0:
        return {}

    result = defaultdict[int, list[str]](lambda: ["", ""])
    lists_by_lang = text.text[index]

    for lang, text_list in enumerate(lists_by_lang):
        for item in text_list:
            id_str: str = item.name.upper().removeprefix("NO")

            try:
                item_id = int(id_str)
                result[item_id][lang] = item.str
            except ValueError:
                print(f"Failed to parse {category} ID {id_str}")

    return result


def _optional_id(item_id: int):
    return item_id if item_id >= 0 else None


def _get_adjusted_id(item_id, link_id_dict):
    if link_id_dict and (link := dict_get(link_id_dict, item_id)):
        return link.bcln.fileId

    return item_id


def _get_file_path_start(item_id):
    if is_ngs(item_id):
        return CharacterMakingDynamic.rebootStart

    return CharacterMakingDynamic.classicStart


def _get_names(name_dict: NameDict, item_id: int):
    try:
        return name_dict[item_id]
    except KeyError:
        return ["", ""]


def _common_props(object_type: ObjectType, item_id: int, name_dict, link_id_dict):
    names = _get_names(name_dict, item_id)
    return {
        "object_type": object_type,
        "id": item_id,
        "adjusted_id": _get_adjusted_id(item_id, link_id_dict),
        "name_jp": names[0],
        "name_en": names[1],
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
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxBodyObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.head_id = _optional_id(item.body2.headId)
        data.sound_id = _optional_id(item.body2.costumeSoundId)
        data.linked_inner_id = _optional_id(item.body2.linkedInnerId)
        data.linked_outer_id = _optional_id(item.body2.int_3C)

        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""
        data.tex_6 = item.texString6 or ""
        data.leg_length = item.body2.legLength
        data.color_mapping = CmxColorMapping.from_body_obj(item.bodyMaskColorMapping)

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
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxBodyPaint(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_sticker(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxSticker(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex = item.texString or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_skin(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxSkinObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""
        data.tex_6 = item.texString6 or ""
        data.tex_7 = item.texString7 or ""
        data.tex_8 = item.texString8 or ""
        data.tex_9 = item.texString9 or ""
        data.tex_10 = item.texString10 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_face(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxFaceObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""
        data.tex_6 = item.texString6 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_facepaint(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxFacePaint(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_eye(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxEyeObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_eyebrow(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxEyebrowObject(
        **_common_props(object_type, item_id, name_dict, link_id_dict)
    )

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_hair(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxHairObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""
        data.tex_6 = item.texString6 or ""
        data.tex_7 = item.texString7 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_ear(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxEarObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_teeth(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxTeethObject(
        **_common_props(object_type, item_id, name_dict, link_id_dict)
    )

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_horn(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxHornObject(**_common_props(object_type, item_id, name_dict, link_id_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data


def _get_accessory(
    object_type: ObjectType,
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
):
    tag = _get_file_tag(object_type)
    data = CmxAccessory(**_common_props(object_type, item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.node_attach_1 = item.nodeAttach1 or ""
        data.node_attach_2 = item.nodeAttach2 or ""
        data.node_attach_3 = item.nodeAttach3 or ""
        data.node_attach_4 = item.nodeAttach4 or ""
        data.node_attach_5 = item.nodeAttach5 or ""
        data.node_attach_6 = item.nodeAttach6 or ""
        data.node_attach_7 = item.nodeAttach7 or ""
        data.node_attach_8 = item.nodeAttach8 or ""
        data.node_attach_9 = item.nodeAttach9 or ""
        data.node_attach_10 = item.nodeAttach10 or ""
        data.node_attach_11 = item.nodeAttach11 or ""
        data.node_attach_12 = item.nodeAttach12 or ""
        data.node_attach_13 = item.nodeAttach13 or ""
        data.node_attach_14 = item.nodeAttach14 or ""
        data.node_attach_15 = item.nodeAttach15 or ""
        data.node_attach_16 = item.nodeAttach16 or ""
        data.node_attach_17 = item.nodeAttach17 or ""
        data.node_attach_18 = item.nodeAttach18 or ""
        data.effect_name = item.effectName or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{tag}_{data.adjusted_id:05d}.ice"

    return data
