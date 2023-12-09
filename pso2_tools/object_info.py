from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
from typing import Optional, TypeVar

try:
    from enum import StrEnum
except ImportError:
    from .strenum import StrEnum

_T = TypeVar("_T")


def _try_parse(obj_type: type[_T], value: str) -> Optional[_T]:
    try:
        return obj_type(value)
    except ValueError:
        return None


class ObjectCategory(StrEnum):
    EFFECT = "eff"
    ENEMY = "en"
    MAG = "mg"
    OBJECT = "ob"
    PLAYER = "pl"
    WEAPON = "wp"
    UI = "ui"


class ObjectType(StrEnum):
    ACCESSORY = "ah"
    BODY = "bd"
    BODY_PAINT = "ba"
    EAR = "ea"
    EYE = "ey"
    EYEBROW = "eb"
    EYELASHES = "es"
    HAIR = "hr"
    HEAD = "hd"
    FACE_PAINT = "hs"
    STICKER = "bp"

    NGS = "r"
    NGS_ACCESSORY = "rah"
    NGS_BODY = "rbd"
    NGS_BODY_PAINT = "rba"
    NGS_EAR = "rea"
    NGS_EYE = "rey"
    NGS_EYEBROW = "reb"
    NGS_EYELASHES = "res"
    NGS_FACE_PAINT = "rfp"
    NGS_HAIR = "rhr"
    NGS_HEAD = "rhd"
    NGS_HORN = "rhn"
    NGS_TEETH = "rdt"


class ModelPart(StrEnum):
    FEMALE_ANY = "fm_xx"
    FEMALE_BASEWEAR = "fl_bw"
    FEMALE_INNERWEAR = "fl_iw"
    FEMALE_OUTERWEAR = "fl_ow"
    FEMALE_COSTUME = "fu_xx"
    FEMALE_FACE = "fm_nh"
    UNKNOWN_FD = "fd_xx"
    MALE_ANY = "ml_xx"
    MALE_BASEWEAR = "ml_bw"
    MALE_INNERWEAR = "ml_iw"
    MALE_OUTERWEAR = "ml_ow"
    MALE_COSTUME = "mu_xx"
    MALE_FACE = "mh_nh"
    UNKNOWN_MA = "ma_xx"
    UNKNOWN_MD = "md_xx"
    FEMALE_CAST_ANY = "fc_xx"
    FEMALE_CAST_ARMS = "fc_rm"
    FEMALE_CAST_BODY = "fc_tr"
    FEMALE_CAST_LEGS = "fc_lg"
    FEMALE_CAST_HEAD = "fc_nh"
    MALE_CAST_ANY = "mc_xx"
    MALE_CAST_ARMS = "mc_rm"
    MALE_CAST_BODY = "mc_tr"
    MALE_CAST_LEGS = "mc_lg"
    MALE_CAST_HEAD = "mc_nh"
    UNKNOWN_UU = "uu_xx"

    NGS_SKIN = "sk"
    NGS_BASEWEAR = "bw"
    NGS_INNERWEAR = "iw"
    NGS_OUTERWEAR = "ow"
    NGS_CAST_ARMS = "rm"
    NGS_CAST_BODY = "bd"
    NGS_CAST_LEGS = "lg"


class TextureId(StrEnum):
    ALPHAS = "a"
    DIFFUSE = "d"
    LAYER = "l"
    MULIT = "m"
    NORMAL = "n"
    SPECULAR = "s"
    UNKNOWN_C = "c"
    UNKNOWN_G = "g"
    UNKNOWN_O = "o"
    UNKNOWN_P = "p"
    UNKNOWN_V = "v"


class BodyType(StrEnum):
    GENDERLESS = "GENDERLESS"
    MALE = "MALE"
    FEMALE = "FEMALE"
    NGS_MALE = "T1"
    NGS_FEMALE = "T2"


_LOD_L1 = "_l1"
_LOD_L2 = "_l2"
_LOD_L3 = "_l3"
_TEXTURE_EXT = (".dds", ".png")


@dataclass
class UVMapping:
    from_u_min: float = 0
    from_u_max: float = 1
    to_u_min: float = 0
    to_u_max: float = 1


CAST_ARMS_UV_MAPPING = UVMapping(from_u_max=1 / 3, to_u_max=2 / 3)
CAST_BODY_UV_MAPPING = UVMapping(from_u_min=1 / 3, from_u_max=2 / 3, to_u_max=2 / 3)
CAST_LEGS_UV_MAPPING = UVMapping(from_u_min=2 / 3, to_u_max=2 / 3)

BODY_OBJECTS = (
    ObjectType.BODY,
    ObjectType.BODY_PAINT,
    ObjectType.NGS_BODY,
    ObjectType.NGS_BODY_PAINT,
)
HAIR_OBJECTS = (ObjectType.HAIR, ObjectType.NGS_HAIR)
HEAD_OBJECTS = (
    ObjectType.EAR,
    ObjectType.HEAD,
    ObjectType.NGS_EAR,
    ObjectType.NGS_HEAD,
)
EYE_OBJECTS = (ObjectType.EYE, ObjectType.NGS_EYE)
EYEBROW_OBJECTS = (ObjectType.EYEBROW, ObjectType.NGS_EYEBROW)
EYELASH_OBJECTS = (ObjectType.EYELASHES, ObjectType.NGS_EYELASHES)

BASEWEAR_PARTS = (
    ModelPart.NGS_BASEWEAR,
    ModelPart.MALE_BASEWEAR,
    ModelPart.FEMALE_BASEWEAR,
)
OUTERWEAR_PARTS = (
    ModelPart.NGS_OUTERWEAR,
    ModelPart.MALE_OUTERWEAR,
    ModelPart.FEMALE_OUTERWEAR,
)
INNERWEAR_PARTS = (
    ModelPart.NGS_INNERWEAR,
    ModelPart.MALE_INNERWEAR,
    ModelPart.FEMALE_INNERWEAR,
)

CAST_ARMS_PARTS = (
    ModelPart.FEMALE_CAST_ARMS,
    ModelPart.MALE_CAST_ARMS,
    ModelPart.NGS_CAST_ARMS,
)
CAST_BODY_PARTS = (
    ModelPart.FEMALE_CAST_BODY,
    ModelPart.MALE_CAST_BODY,
    ModelPart.NGS_CAST_BODY,
)
CAST_LEGS_PARTS = (
    ModelPart.FEMALE_CAST_LEGS,
    ModelPart.MALE_CAST_LEGS,
    ModelPart.NGS_CAST_LEGS,
)
CAST_PARTS = (
    *CAST_ARMS_PARTS,
    *CAST_BODY_PARTS,
    *CAST_LEGS_PARTS,
    ModelPart.FEMALE_CAST_ANY,
    ModelPart.MALE_CAST_ANY,
)

MALE_COSTUME_IDS = (0, 9999)
FEMALE_COSTUME_IDS = (10000, 19999)
MALE_BASEWEAR_IDS = (20000, 29999)
FEMALE_BASEWEAR_IDS = (30000, 39999)
MALE_CAST_IDS = (40000, 49999)
FEMALE_CAST_IDS = (50000, 59999)

NGS_T1_IDS = (100000, 199999)
NGS_T2_IDS = (200000, 299999)
NGS_T1_CAST_IDS = (300000, 399999)
NGS_T2_CAST_IDS = (400000, 499999)
NGS_GENDERLESS_IDS = (500000, 599999)

NGS_BASE_BODY_ICE: dict[BodyType, str] = {
    BodyType.NGS_MALE: "195fac68420e7a08fb37ae36403a419b",
    BodyType.NGS_FEMALE: "be23da464641f6ea102f4366095fa5eb",
}


@dataclass
class ObjectInfo:
    name: str = ""
    extension: str = ""
    category: Optional[ObjectCategory] = None
    object_type: Optional[ObjectType] = None
    object_id: int = 0
    part: Optional[ObjectType] = None
    texture: Optional[str] = None
    level_of_detail: int = 0

    @classmethod
    def from_file_name(cls, path: str | Path):
        # category_...

        try:
            path = Path(path)
            category, _, rest = path.with_suffix("").name.partition("_")
        except ValueError:
            return ObjectInfo(name=path.name)

        info = ObjectInfo(name=path.name, extension=path.suffix, category=category)

        match info.category:
            case ObjectCategory.MAG:
                # TODO: mags have similar names to weapons
                info._from_weapon_file_name(rest)

            case ObjectCategory.OBJECT:
                info._from_object_file_name(rest)

            case ObjectCategory.PLAYER:
                info._from_player_file_name(rest)

            case ObjectCategory.WEAPON:
                info._from_weapon_file_name(rest)

        return info

    @property
    def description(self) -> str:
        return _get_description(self)

    @property
    def body_type(self) -> BodyType:
        if self.id_in_ranges(NGS_T1_IDS, NGS_T1_CAST_IDS):
            return BodyType.NGS_MALE

        if self.id_in_ranges(NGS_T2_IDS, NGS_T2_CAST_IDS):
            return BodyType.NGS_FEMALE

        if self.id_in_ranges(MALE_COSTUME_IDS, MALE_BASEWEAR_IDS, MALE_CAST_IDS):
            return BodyType.MALE

        if self.id_in_ranges(FEMALE_COSTUME_IDS, FEMALE_BASEWEAR_IDS, FEMALE_CAST_IDS):
            return BodyType.FEMALE

        return BodyType.GENDERLESS

    @property
    def base_body_ice(self) -> Optional[str]:
        return NGS_BASE_BODY_ICE.get(self.body_type)

    @property
    def is_ngs(self):
        return self.object_type is not None and str(self.object_type).startswith("r")

    @property
    def is_body_object(self):
        return (
            self.category == ObjectCategory.PLAYER and self.object_type in BODY_OBJECTS
        )

    @property
    def is_basewear(self):
        return self.category == ObjectCategory.PLAYER and self.part in BASEWEAR_PARTS

    @property
    def is_outerwear(self):
        return self.category == ObjectCategory.PLAYER and self.part in OUTERWEAR_PARTS

    @property
    def is_innerwear(self):
        return self.category == ObjectCategory.PLAYER and self.part in INNERWEAR_PARTS

    @property
    def is_cast_part(self):
        return self.is_body_object and self.part in CAST_PARTS

    @property
    def is_hair(self):
        return (
            self.category == ObjectCategory.PLAYER and self.object_type in HAIR_OBJECTS
        )

    @property
    def is_head(self):
        return (
            self.category == ObjectCategory.PLAYER and self.object_type in HEAD_OBJECTS
        )

    @property
    def is_eye(self):
        return (
            self.category == ObjectCategory.PLAYER and self.object_type in EYE_OBJECTS
        )

    @property
    def is_eyebrow(self):
        return (
            self.category == ObjectCategory.PLAYER
            and self.object_type in EYEBROW_OBJECTS
        )

    @property
    def is_eyelash(self):
        return (
            self.category == ObjectCategory.PLAYER
            and self.object_type in EYELASH_OBJECTS
        )

    @property
    def use_costume_colors(self):
        return self.is_body_object and not self.part in CAST_PARTS

    @property
    def use_skin_colors(self):
        return self.is_body_object or self.is_head

    @property
    def use_cast_colors(self):
        return self.is_cast_part

    @property
    def use_hair_colors(self):
        return self.is_hair

    @property
    def use_eye_colors(self):
        return self.is_eye

    @property
    def use_eyebrow_colors(self):
        return self.is_eyebrow

    @property
    def use_eyelash_colors(self):
        return self.is_eyelash

    @property
    def uv_mapping(self) -> Optional[UVMapping]:
        if self.part in CAST_ARMS_PARTS:
            return CAST_ARMS_UV_MAPPING
        if self.part in CAST_BODY_PARTS:
            return CAST_BODY_UV_MAPPING
        if self.part in CAST_LEGS_PARTS:
            return CAST_LEGS_UV_MAPPING
        return None

    def id_in_ranges(self, *bounds: list[tuple[int, int]]):
        return any(b[0] <= self.object_id <= b[1] for b in bounds)

    def _from_object_file_name(self, rest: str):
        # One of
        # ..._####_####.ext
        # ..._####_####_lod.ext
        # ..._####_####_motion.ext
        # ..._####_####_###_texture.ext

        rest, lod = _partition_lod(rest)
        self.level_of_detail = lod

        if self.extension in _TEXTURE_EXT:
            rest, _, texture = rest.rpartition("_")
            self.texture = _try_parse(TextureId, texture)

    def _from_player_file_name(self, rest: str):
        # ..._type_id_...
        object_type, _, rest = rest.partition("_")
        object_id, _, rest = rest.partition("_")

        self.object_type = _try_parse(ObjectType, object_type)
        self.object_id = _try_parse(int, object_id)

        if self.is_ngs:
            # One of
            # ..._part.ext
            # ..._texture.ext
            # ..._part_texture.ext
            # ..._part_lod.ext

            rest, lod = _partition_lod(rest)
            self.level_of_detail = lod

            if self.extension in _TEXTURE_EXT:
                part, _, texture = rest.rpartition("_")
                self.texture = _try_parse(TextureId, texture)
            else:
                part = rest

            self.part = _try_parse(ModelPart, part)
        else:
            # ...texture_part_part.ext
            texture, _, part = rest.partition("_")

            if texture != "x":
                self.texture = _try_parse(TextureId, texture)

            if part != "xx_xx":
                self.part = _try_parse(ModelPart, part)

    def _from_weapon_file_name(self, rest: str):
        # ...[_r]_##_##_##_##_##_r[_texture].ext

        if rest.startswith(ObjectType.NGS):
            self.object_type = ObjectType.NGS

        if self.extension in _TEXTURE_EXT:
            rest, _, texture = rest.rpartition("_")
            self.texture = _try_parse(TextureId, texture)


def _partition_lod(text: str) -> tuple[str, int]:
    if text.endswith(_LOD_L1):
        return text.removesuffix(_LOD_L1), 1

    if text.endswith(_LOD_L2):
        return text.removesuffix(_LOD_L2), 2

    if text.endswith(_LOD_L3):
        return text.removesuffix(_LOD_L3), 1

    return text, 0


def _get_description(info: ObjectInfo):
    tag = " (NGS)" if info.is_ngs else ""

    match info:
        case ObjectInfo(category=ObjectCategory.EFFECT):
            return "Effect"

        case ObjectInfo(category=ObjectCategory.ENEMY):
            return f"Enemy{tag}"

        case ObjectInfo(category=ObjectCategory.MAG):
            return f"Mag{tag}"

        case ObjectInfo(category=ObjectCategory.WEAPON):
            return f"Weapon{tag}"

        case ObjectInfo(category=ObjectCategory.UI):
            return "UI"

        # Player objects
        case ObjectInfo(object_type=ObjectType.ACCESSORY):
            return "Accessory"

        case ObjectInfo(object_type=ObjectType.NGS_ACCESSORY):
            return "Accessory (NGS)"

        case ObjectInfo(object_type=ObjectType.BODY_PAINT):
            return "Body Paint"

        case ObjectInfo(object_type=ObjectType.NGS_BODY_PAINT):
            return "Body Paint (NGS)"

        case ObjectInfo(object_type=ObjectType.EAR):
            return "Ears"

        case ObjectInfo(object_type=ObjectType.NGS_EAR):
            return "Ears (NGS)"

        case ObjectInfo(object_type=ObjectType.EYE):
            return "Eyes"

        case ObjectInfo(object_type=ObjectType.NGS_EYE):
            return "Eyes (NGS)"

        case ObjectInfo(object_type=ObjectType.EYEBROW):
            return "Eyebrows"

        case ObjectInfo(object_type=ObjectType.NGS_EYEBROW):
            return "Eyebrows (NGS)"

        case ObjectInfo(object_type=ObjectType.EYELASHES):
            return "Eyelashes"

        case ObjectInfo(object_type=ObjectType.NGS_EYELASHES):
            return "Eyelashes (NGS)"

        case ObjectInfo(object_type=ObjectType.HAIR):
            return "Hair"

        case ObjectInfo(object_type=ObjectType.NGS_HAIR):
            return "Hair (NGS)"

        case ObjectInfo(object_type=ObjectType.HEAD):
            return "Head"

        case ObjectInfo(object_type=ObjectType.NGS_HEAD):
            return "Head (NGS)"

        case ObjectInfo(object_type=ObjectType.FACE_PAINT):
            return "Face Paint"

        case ObjectInfo(object_type=ObjectType.NGS_FACE_PAINT):
            return "Face Paint (NGS)"

        case ObjectInfo(object_type=ObjectType.NGS_HORN):
            return "Horns (NGS)"

        case ObjectInfo(object_type=ObjectType.NGS_TEETH):
            return "Teeth (NGS)"

        case ObjectInfo(object_type=ObjectType.STICKER):
            return "Sticker"

        case ObjectInfo(object_type=ObjectType.BODY, part=part):
            return _get_part_description(part)

        case ObjectInfo(object_type=ObjectType.NGS_BODY, part=part):
            return _get_part_description(part)

    return ""


_MODEL_PART_DESCRIPTIONS: dict[ModelPart, str] = {
    ModelPart.FEMALE_BASEWEAR: "Female Basewear",
    ModelPart.FEMALE_INNERWEAR: "Female Innerwear",
    ModelPart.FEMALE_OUTERWEAR: "Female Outerwear",
    ModelPart.FEMALE_COSTUME: "Female Costume",
    ModelPart.FEMALE_FACE: "Female Face",
    ModelPart.MALE_BASEWEAR: "Male Basewear",
    ModelPart.MALE_INNERWEAR: "Male Innerwear",
    ModelPart.MALE_OUTERWEAR: "Male Outerwear",
    ModelPart.MALE_COSTUME: "Male Costume",
    ModelPart.MALE_FACE: "Male Face",
    ModelPart.FEMALE_CAST_ARMS: "Female Cast Arms",
    ModelPart.FEMALE_CAST_BODY: "Female Cast Body",
    ModelPart.FEMALE_CAST_LEGS: "Female Cast Legs",
    ModelPart.FEMALE_CAST_HEAD: "Female Cast Head",
    ModelPart.MALE_CAST_ARMS: "Male Cast Arms",
    ModelPart.MALE_CAST_BODY: "Male Cast Body",
    ModelPart.MALE_CAST_LEGS: "Male Cast Legs",
    ModelPart.MALE_CAST_HEAD: "Male Cast Head",
    ModelPart.NGS_SKIN: "Skin (NGS)",
    ModelPart.NGS_BASEWEAR: "Basewear (NGS)",
    ModelPart.NGS_INNERWEAR: "Innerwear (NGS)",
    ModelPart.NGS_OUTERWEAR: "Outerwear (NGS)",
    ModelPart.NGS_CAST_ARMS: "Cast Arms (NGS)",
    ModelPart.NGS_CAST_BODY: "Cast Body (NGS)",
    ModelPart.NGS_CAST_LEGS: "Cast Legs (NGS)",
}


def _get_part_description(part: ModelPart):
    return _MODEL_PART_DESCRIPTIONS.get(part, "")
