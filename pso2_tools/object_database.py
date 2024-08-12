import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field, fields
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Optional, Type, TypeVar, overload

import bpy
from AquaModelLibrary.Data.PSO2.Aqua import PSO2Text
from AquaModelLibrary.Data.PSO2.Constants import CharacterMakingDynamic
from AquaModelLibrary.Data.Utility import ReferenceGenerator
from AquaModelLibrary.Helpers import HashHelpers

from . import preferences
from .colors import ColorId
from .paths import DATA_PATH
from .util import dict_get

T = TypeVar("T")
NameDict = dict[int, list[str]]


class Table(StrEnum):
    ACCESSORIES = "accessories"
    COSTUMES = "costumes"
    BASEWEAR = "basewear"
    OUTERWEAR = "outerwear"
    CAST_ARMS = "cast_arms"
    CAST_BODIES = "cast_bodies"
    CAST_LEGS = "cast_legs"
    INNERWEAR = "innerwear"
    BODYPAINT = "bodypaint"
    STICKERS = "stickers"
    SKINS = "skins"
    FACES = "faces"
    FACE_TEXTURES = "face_textures"
    FACEPAINT = "facepaint"
    EYES = "eyes"
    EYEBROWS = "eyebrows"
    EYELASHES = "eyelashes"
    EARS = "ears"
    TEETH = "teeth"
    HORNS = "horns"
    HAIR = "hair"


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
    LEG = "leg"
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

    @classmethod
    def from_body_obj(cls, obj):
        return cls(
            red=ColorId(int(obj.redIndex)),
            green=ColorId(int(obj.greenIndex)),
            blue=ColorId(int(obj.blueIndex)),
            alpha=ColorId(int(obj.alphaIndex)),
        )


def convert_color_map(text: str):
    r, g, b, a = text.split(";")
    return CmxColorMapping(
        red=ColorId(r), green=ColorId(g), blue=ColorId(b), alpha=ColorId(a)
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
    def reboot_hash(self):
        name = self.hash
        return name[0:2] + "/" + name[2:]

    @property
    def ex(self):
        start: str = CharacterMakingDynamic.rebootStart
        ex: str = CharacterMakingDynamic.rebootExStart

        if not self.name.startswith(start):
            return CmxFileName()

        name = self.name.replace(start, ex).replace(".ice", "_ex.ice")
        return CmxFileName(name)

    def path(self, data_path: Path, is_reboot=False):
        name = self.reboot_hash if is_reboot else self.hash
        return data_path / name


def convert_file_name(text: str):
    return CmxFileName(text)


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
    id: int
    adjusted_id: int
    name_en: str = ""
    name_jp: str = ""

    @property
    def name(self):
        return self.name_en or self.name_jp or f"Unnamed {self.id}"

    @property
    def type(self):
        return CmxPartType.from_id(self.id)

    @classmethod
    def from_db_row(cls, row: sqlite3.Row):
        d = {k: row[k] for k in row.keys()}

        return cls(**d)

    @classmethod
    def db_schema(cls, table: Table):
        columns = [
            f"{field.name} {_db_type(field.type)} {_db_attr(field.name)}"
            for field in fields(cls)
        ]

        return f"CREATE TABLE {table}( {','.join(columns)} );"

    def db_insert(self, con: sqlite3.Connection, table: Table):
        d = {field.name: getattr(self, field.name) for field in fields(self)}

        placeholders = ",".join(":" + k for k in d.keys())

        con.execute(f"INSERT INTO {table} VALUES({placeholders})", d)


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
    head_item_id: Optional[int] = None
    sound_item_id: Optional[int] = None
    linked_inner_item_id: Optional[int] = None
    linked_outer_item_id: Optional[int] = None

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


@dataclass
class CmxFaceObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""
    tex_6: str = ""


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


@dataclass
class CmxEyebrowObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""


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


@dataclass
class CmxEarObject(CmxObjectBase):
    file: CmxFileName = field(default_factory=CmxFileName)
    tex_1: str = ""
    tex_2: str = ""
    tex_3: str = ""
    tex_4: str = ""
    tex_5: str = ""


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

    def get_accessories(self, item_id: Optional[int] = None):
        return self._get_objects(CmxAccessory, Table.ACCESSORIES, item_id)

    def get_costumes(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, Table.COSTUMES, item_id)

    def get_basewear(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, Table.BASEWEAR, item_id)

    def get_outerwear(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, Table.OUTERWEAR, item_id)

    def get_cast_arms(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, Table.CAST_ARMS, item_id)

    def get_cast_bodies(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, Table.CAST_BODIES, item_id)

    def get_cast_legs(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyObject, Table.CAST_LEGS, item_id)

    def get_innerwear(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyPaint, Table.INNERWEAR, item_id)

    def get_bodypaint(self, item_id: Optional[int] = None):
        return self._get_objects(CmxBodyPaint, Table.BODYPAINT, item_id)

    def get_stickers(self, item_id: Optional[int] = None):
        return self._get_objects(CmxSticker, Table.STICKERS, item_id)

    def get_skins(self, item_id: Optional[int] = None):
        return self._get_objects(CmxSkinObject, Table.SKINS, item_id)

    def get_faces(self, item_id: Optional[int] = None):
        return self._get_objects(CmxFaceObject, Table.FACES, item_id)

    def get_face_textures(self, item_id: Optional[int] = None):
        return self._get_objects(CmxFacePaint, Table.FACE_TEXTURES, item_id)

    def get_facepaint(self, item_id: Optional[int] = None):
        return self._get_objects(CmxFacePaint, Table.FACEPAINT, item_id)

    def get_eyes(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEyeObject, Table.EYES, item_id)

    def get_eyebrows(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEyebrowObject, Table.EYEBROWS, item_id)

    def get_eyelashes(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEyebrowObject, Table.EYELASHES, item_id)

    def get_ears(self, item_id: Optional[int] = None):
        return self._get_objects(CmxEarObject, Table.EARS, item_id)

    def get_teeth(self, item_id: Optional[int] = None):
        return self._get_objects(CmxTeethObject, Table.TEETH, item_id)

    def get_horns(self, item_id: Optional[int] = None):
        return self._get_objects(CmxHornObject, Table.HORNS, item_id)

    def get_hair(self, item_id: Optional[int] = None):
        return self._get_objects(CmxHairObject, Table.HAIR, item_id)

    def _get_objects(
        self, cls: Type[T], table: str, item_id: Optional[int] = None
    ) -> list[T]:
        if id is not None:
            return [
                cls.from_db_row(row)
                for row in self.con.execute(f"SELECT * FROM {table} WHERE id=?", (id,))
            ]

        return [
            cls.from_db_row(row) for row in self.con.execute(f"SELECT * FROM {table}")
        ]

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
            self._read_costumes(cmx, parts_text)
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
        path = DATA_PATH / "objects.db"
        path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: Remove once database schema is stable
        if path.exists():
            path.unlink()

        con = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        con.row_factory = sqlite3.Row

        with con:
            version = con.execute("PRAGMA user_version").fetchone()[0]

            if version < 1:
                con.executescript(
                    f"""
                    {CmxAccessory.db_schema(Table.ACCESSORIES)}
                    {CmxBodyObject.db_schema(Table.COSTUMES)}
                    {CmxBodyObject.db_schema(Table.BASEWEAR)}
                    {CmxBodyObject.db_schema(Table.OUTERWEAR)}
                    {CmxBodyObject.db_schema(Table.CAST_BODIES)}
                    {CmxBodyObject.db_schema(Table.CAST_ARMS)}
                    {CmxBodyObject.db_schema(Table.CAST_LEGS)}
                    {CmxBodyPaint.db_schema(Table.INNERWEAR)}
                    {CmxBodyPaint.db_schema(Table.BODYPAINT)}
                    {CmxSticker.db_schema(Table.STICKERS)}
                    {CmxSkinObject.db_schema(Table.SKINS)}
                    {CmxFaceObject.db_schema(Table.FACES)}
                    {CmxFacePaint.db_schema(Table.FACE_TEXTURES)}
                    {CmxFacePaint.db_schema(Table.FACEPAINT)}
                    {CmxEyeObject.db_schema(Table.EYES)}
                    {CmxEyebrowObject.db_schema(Table.EYEBROWS)}
                    {CmxEyebrowObject.db_schema(Table.EYELASHES)}
                    {CmxEarObject.db_schema(Table.EARS)}
                    {CmxTeethObject.db_schema(Table.TEETH)}
                    {CmxHornObject.db_schema(Table.HORNS)}
                    {CmxHairObject.db_schema(Table.HAIR)}
                    """
                )

            con.execute("PRAGMA user_version=1")

        return con

    def _reset_db(self):
        for table in Table:
            self.con.execute(f"DELETE FROM {table}")

    def _read_accessories(self, cmx, text):
        names = _get_item_names(text, CmxCategory.ACCESSORY)
        for item_id in cmx.accessoryDict.Keys:
            obj = _get_accessory(
                cmx.accessoryDict, cmx.accessoryIdLink, names, item_id, "ac"
            )
            obj.db_insert(self.con, Table.ACCESSORIES)

    def _read_cast_arms(self, cmx, text):
        names = _get_item_names(text, CmxCategory.ARM)
        for item_id in cmx.carmDict.Keys:
            obj = _get_body(cmx.carmDict, cmx.castArmIdLink, names, item_id, "am")
            obj.db_insert(self.con, Table.CAST_ARMS)

    def _read_cast_legs(self, cmx, text):
        names = _get_item_names(text, CmxCategory.ARM)
        for item_id in cmx.clegDict.Keys:
            obj = _get_body(cmx.clegDict, cmx.clegIdLink, names, item_id, "lg")
            obj.db_insert(self.con, Table.CAST_LEGS)

    def _read_costumes(self, cmx, text):
        names = _get_item_names(text, CmxCategory.COSTUME)
        names.update(_get_item_names(text, CmxCategory.BODY))

        for item_id in cmx.costumeDict.Keys:
            obj = _get_body(cmx.costumeDict, cmx.costumeIdLink, names, item_id, "bd")
            if item_id < 40000:
                obj.db_insert(self.con, Table.COSTUMES)
            else:
                obj.db_insert(self.con, Table.CAST_BODIES)

    def _read_basewear(self, cmx, text):
        names = _get_item_names(text, CmxCategory.BASEWEAR)
        for item_id in cmx.baseWearDict.Keys:
            obj = _get_body(cmx.baseWearDict, cmx.baseWearIdLink, names, item_id, "bw")
            obj.db_insert(self.con, Table.BASEWEAR)

    def _read_outerwear(self, cmx, text):
        names = _get_item_names(text, CmxCategory.COSTUME)
        for item_id in cmx.outerDict.Keys:
            obj = _get_body(cmx.outerDict, cmx.outerWearIdLink, names, item_id, "ow")
            obj.db_insert(self.con, Table.OUTERWEAR)

    def _read_innerwear(self, cmx, text):
        names = _get_item_names(text, CmxCategory.INNERWEAR)
        for item_id in cmx.innerWearDict.Keys:
            obj = _get_bodypaint(
                cmx.innerWearDict, cmx.innerWearIdLink, names, item_id, "iw"
            )
            obj.db_insert(self.con, Table.INNERWEAR)

    def _read_bodypaint(self, cmx, text):
        names = _get_item_names(text, CmxCategory.BODYPAINT1)
        for item_id in cmx.bodyPaintDict.Keys:
            obj = _get_bodypaint(cmx.bodyPaintDict, None, names, item_id, "b1")
            obj.db_insert(self.con, Table.BODYPAINT)

    def _read_stickers(self, cmx, text):
        names = _get_item_names(text, CmxCategory.BODYPAINT2)
        for item_id in cmx.stickerDict.Keys:
            obj = _get_sticker(cmx.stickerDict, None, names, item_id, "b2")
            obj.db_insert(self.con, Table.STICKERS)

    def _read_skins(self, cmx, text):
        names = _get_item_names(text, CmxCategory.SKIN)
        for item_id in cmx.ngsSkinDict.Keys:
            obj = _get_skin(cmx.ngsSkinDict, None, names, item_id, "sk")
            obj.db_insert(self.con, Table.SKINS)

    def _read_faces(self, cmx, text):
        names = _get_item_names(text, CmxCategory.FACE)
        # TODO: need to parse face_variation.cmp.lua in 75b1632526cd6a1039625349df6ee8dd
        # names.update(_get_item_names(text, CmxCategory.FACE_VARIATION))

        for item_id in cmx.faceDict.Keys:
            obj = _get_face(cmx.faceDict, None, names, item_id, "fc")
            obj.db_insert(self.con, Table.FACES)

    def _read_face_textures(self, cmx, text):
        names = _get_item_names(text, CmxCategory.FACEPAINT1)
        for item_id in cmx.faceTextureDict.Keys:
            obj = _get_facepaint(cmx.faceTextureDict, None, names, item_id, "f1")
            obj.db_insert(self.con, Table.FACE_TEXTURES)

    def _read_facepaint(self, cmx, text):
        names = _get_item_names(text, CmxCategory.FACEPAINT2)
        for item_id in cmx.fcpDict.Keys:
            obj = _get_facepaint(cmx.fcpDict, None, names, item_id, "f2")
            obj.db_insert(self.con, Table.FACEPAINT)

    def _read_eyes(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EYE)
        for item_id in cmx.eyeDict.Keys:
            obj = _get_eye(cmx.eyeDict, None, names, item_id, "ey")
            obj.db_insert(self.con, Table.EYES)

    def _read_eyebrows(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EYEBROWS)
        for item_id in cmx.eyebrowDict.Keys:
            obj = _get_eyebrow(cmx.eyebrowDict, None, names, item_id, "eb")
            obj.db_insert(self.con, Table.EYEBROWS)

    def _read_eyelashes(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EYELASHES)
        for item_id in cmx.eyelashDict.Keys:
            obj = _get_eyebrow(cmx.eyelashDict, None, names, item_id, "el")
            obj.db_insert(self.con, Table.EYELASHES)

    def _read_hair(self, cmx, text):
        names = _get_item_names(text, CmxCategory.HAIR)
        for item_id in cmx.hairDict.Keys:
            obj = _get_hair(cmx.hairDict, None, names, item_id, "hr")
            obj.db_insert(self.con, Table.HAIR)

    def _read_ears(self, cmx, text):
        names = _get_item_names(text, CmxCategory.EARS)
        for item_id in cmx.ngsEarDict.Keys:
            obj = _get_ear(cmx.ngsEarDict, None, names, item_id, "ea")
            obj.db_insert(self.con, Table.EARS)

    def _read_teeth(self, cmx, text):
        names = _get_item_names(text, CmxCategory.TEETH)
        for item_id in cmx.ngsTeethDict.Keys:
            obj = _get_teeth(cmx.ngsTeethDict, None, names, item_id, "de")
            obj.db_insert(self.con, Table.TEETH)

    def _read_horns(self, cmx, text):
        names = _get_item_names(text, CmxCategory.HORN)
        for item_id in cmx.ngsHornDict.Keys:
            obj = _get_horn(cmx.ngsHornDict, None, names, item_id, "hn")
            obj.db_insert(self.con, Table.HORNS)


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


def _is_ngs(item_id):
    return item_id >= 100000


def _get_file_path_start(item_id):
    if _is_ngs(item_id):
        return CharacterMakingDynamic.rebootStart

    return CharacterMakingDynamic.classicStart


def _get_names(name_dict: NameDict, item_id: int):
    try:
        return name_dict[item_id]
    except KeyError:
        return ["", ""]


def _get_base_cmx_props(item_id, name_dict, link_id_dict):
    names = _get_names(name_dict, item_id)
    return {
        "id": item_id,
        "adjusted_id": _get_adjusted_id(item_id, link_id_dict),
        "name_jp": names[0],
        "name_en": names[1],
    }


def _get_body(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxBodyObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

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

    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    if data.linked_inner_id is not None:
        data.linked_inner_file.name = f"{start}b1_{data.adjusted_id:05d}.ice"

    if data.linked_outer_id is not None:
        data.linked_outer_file.name = f"{start}ow_{data.adjusted_id:05d}.ice"

    if data.sound_id is not None:
        data.sound_file.name = f"{start}bs_{data.adjusted_id:05d}.ice"
        data.cast_sound_file.name = f"{start}ls_{data.adjusted_id:05d}.ice"

    return data


def _get_bodypaint(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxBodyPaint(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_sticker(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxSticker(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex = item.texString or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_skin(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxSkinObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

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
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_face(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxFaceObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""
        data.tex_6 = item.texString6 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_facepaint(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxFacePaint(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_eye(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxEyeObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_eyebrow(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxEyebrowObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_hair(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxHairObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""
        data.tex_6 = item.texString6 or ""
        data.tex_7 = item.texString7 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_ear(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxEarObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""
        data.tex_5 = item.texString5 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_teeth(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxTeethObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    if item := dict_get(object_dict, item_id):
        data.tex_1 = item.texString1 or ""
        data.tex_2 = item.texString2 or ""
        data.tex_3 = item.texString3 or ""
        data.tex_4 = item.texString4 or ""

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_horn(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxHornObject(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

    start = _get_file_path_start(item_id)
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data


def _get_accessory(
    object_dict,
    link_id_dict,
    name_dict: NameDict,
    item_id: int,
    file_type: str,
):
    data = CmxAccessory(**_get_base_cmx_props(item_id, name_dict, link_id_dict))

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
    data.file.name = f"{start}{file_type}_{data.adjusted_id:05d}.ice"

    return data
