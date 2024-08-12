from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple

Color = Tuple[float, float, float, float]

WHITE: Color = (1, 1, 1, 1)
GRAY: Color = (0.5, 0.5, 0.5, 1)
BLACK: Color = (0, 0, 0, 1)
MAGENTA: Color = (1, 0, 1, 1)

DEFAULT_MAIN_SKIN: Color = (0.8, 0.42, 0.30, 1)
DEFAULT_SUB_SKIN: Color = (1, 0.02, 0.02, 1)
DEFAULT_HAIR_1: Color = (1, 0.49, 0.14, 1)
DEFAULT_HAIR_2: Color = (1, 0.82, 0.67, 1)
DEFAULT_EYE: Color = (0, 0.85, 0.85, 1)


class ColorId(IntEnum):
    UNUSED = 0
    OUTER1 = 1
    OUTER2 = 2
    BASE1 = 3
    BASE2 = 4
    INNER1 = 5
    INNER2 = 6
    CAST1 = 7
    CAST2 = 8
    CAST3 = 9
    CAST4 = 10
    MAIN_SKIN = 11
    SUB_SKIN = 12
    RIGHT_EYE = 13
    LEFT_EYE = 14
    EYEBROW = 15
    EYELASH = 16
    HAIR1 = 17
    HAIR2 = 18


@dataclass
class ColorChannel:
    group: str
    prop: str
    name: str
    default: Color


COLOR_CHANNELS = {
    ColorId.OUTER1: ColorChannel("Costume", "outer_color_1", "Outerwear 1", GRAY),
    ColorId.OUTER2: ColorChannel("Costume", "outer_color_2", "Outerwear 2", GRAY),
    ColorId.BASE1: ColorChannel("Costume", "base_color_1", "Basewear 1", GRAY),
    ColorId.BASE2: ColorChannel("Costume", "base_color_2", "Basewear 2", GRAY),
    ColorId.INNER1: ColorChannel("Costume", "inner_color_1", "Innerwear 1", GRAY),
    ColorId.INNER2: ColorChannel("Costume", "inner_color_2", "Innerwear 2", GRAY),
    ColorId.CAST1: ColorChannel("Cast Parts", "cast_color_1", "Cast 1", GRAY),
    ColorId.CAST2: ColorChannel("Cast Parts", "cast_color_2", "Cast 2", GRAY),
    ColorId.CAST3: ColorChannel("Cast Parts", "cast_color_3", "Cast 3", GRAY),
    ColorId.CAST4: ColorChannel("Cast Parts", "cast_color_4", "Cast 4", GRAY),
    ColorId.MAIN_SKIN: ColorChannel(
        "Skin", "main_skin_color", "Main Skin", DEFAULT_MAIN_SKIN
    ),
    ColorId.SUB_SKIN: ColorChannel(
        "Skin", "sub_skin_color", "Sub Skin", DEFAULT_SUB_SKIN
    ),
    ColorId.RIGHT_EYE: ColorChannel(
        "Head", "right_eye_color", "Right Eye", DEFAULT_EYE
    ),
    ColorId.LEFT_EYE: ColorChannel("Head", "left_eye_color", "Left Eye", DEFAULT_EYE),
    ColorId.EYEBROW: ColorChannel("Head", "eyebrow_color", "Eyebrow", DEFAULT_HAIR_1),
    ColorId.EYELASH: ColorChannel("Head", "eyelash_color", "Eyelash", DEFAULT_HAIR_1),
    ColorId.HAIR1: ColorChannel("Head", "hair_color_1", "Hair 1", DEFAULT_HAIR_1),
    ColorId.HAIR2: ColorChannel("Head", "hair_color_2", "Hair 2", DEFAULT_HAIR_2),
}
