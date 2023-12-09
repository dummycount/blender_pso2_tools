from dataclasses import dataclass
from enum import Enum
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


class Colors(Enum):
    Unused = 0
    Outer1 = 1
    Outer2 = 2
    Base1 = 3
    Base2 = 4
    Inner1 = 5
    Inner2 = 6
    Cast1 = 7
    Cast2 = 8
    Cast3 = 9
    Cast4 = 10
    MainSkin = 11
    SubSkin = 12
    RightEye = 13
    LeftEye = 14
    Eyebrow = 15
    Eyelash = 16
    Hair1 = 17
    Hair2 = 18


@dataclass
class ColorChannel:
    prop: str
    name: str
    default: Color


COLOR_CHANNELS = {
    Colors.Outer1: ColorChannel("outer_color_1", "Outerwear 1", GRAY),
    Colors.Outer2: ColorChannel("outer_color_2", "Outerwear 2", GRAY),
    Colors.Base1: ColorChannel("base_color_1", "Basewear 1", GRAY),
    Colors.Base2: ColorChannel("base_color_2", "Basewear 2", GRAY),
    Colors.Inner1: ColorChannel("inner_color_1", "Innerwear 1", GRAY),
    Colors.Inner2: ColorChannel("inner_color_2", "Innerwear 2", GRAY),
    Colors.Cast1: ColorChannel("cast_color_1", "Cast 1", GRAY),
    Colors.Cast2: ColorChannel("cast_color_2", "Cast 2", GRAY),
    Colors.Cast3: ColorChannel("cast_color_3", "Cast 3", GRAY),
    Colors.Cast4: ColorChannel("cast_color_4", "Cast 4", GRAY),
    Colors.MainSkin: ColorChannel("main_skin_color", "Main Skin", DEFAULT_MAIN_SKIN),
    Colors.SubSkin: ColorChannel("sub_skin_color", "Sub Skin", DEFAULT_SUB_SKIN),
    Colors.RightEye: ColorChannel("right_eye_color", "Right Eye", DEFAULT_EYE),
    Colors.LeftEye: ColorChannel("left_eye_color", "Left Eye", DEFAULT_EYE),
    Colors.Eyebrow: ColorChannel("eyebrow_color", "Eyebrow", DEFAULT_HAIR_1),
    Colors.Eyelash: ColorChannel("eyelash_color", "Eyelash", DEFAULT_HAIR_1),
    Colors.Hair1: ColorChannel("hair_color_1", "Hair 1", DEFAULT_HAIR_1),
    Colors.Hair2: ColorChannel("hair_color_2", "Hair 2", DEFAULT_HAIR_2),
}
