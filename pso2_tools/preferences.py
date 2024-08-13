import os
import re
from pathlib import Path

import bpy

from . import classes
from .colors import COLOR_CHANNELS, ColorId

PROGRAM_FILES = Path(os.getenv("PROGRAMFILES(x86)"))

WINDOWS_STORE_PATH = PROGRAM_FILES / "ModifiableWindowsApps/pso2_bin/data"
STEAM_PATH = "SteamApps/common/PHANTASYSTARONLINE2_NA_STEAM/pso2_bin/data"


def _get_steam_libraries() -> list[Path]:
    path_re = re.compile(r'\s*"path"\s*"([^"]+)"\s*')
    steam_libraries_file = PROGRAM_FILES / "Steam/SteamApps/libraryfolders.vdf"
    try:
        with steam_libraries_file.open(encoding="utf-8") as f:
            return [Path(m.group(1)) for line in f if (m := path_re.match(line))]
    except OSError:
        return []


def _get_default_data_path() -> str:
    if WINDOWS_STORE_PATH.exists():
        return str(WINDOWS_STORE_PATH)

    for library in _get_steam_libraries():
        steam_path = library / STEAM_PATH
        if steam_path.exists():
            return str(steam_path)

    return ""


def color_property(color: ColorId, description: str):
    channel = COLOR_CHANNELS[color]

    return bpy.props.FloatVectorProperty(
        name=channel.name,
        description=description,
        default=channel.default,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )


@classes.register
class Pso2ToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    pso2_data_path: bpy.props.StringProperty(
        name="Path to pso2_bin/data",
        subtype="DIR_PATH",
        default=_get_default_data_path(),
    )

    debug: bpy.props.BoolProperty(name="Show debug info", default=False)

    outer_color_1: color_property(ColorId.OUTER1, "Primary outerwear color")
    outer_color_2: color_property(ColorId.OUTER2, "Secondary outerwear color")
    base_color_1: color_property(ColorId.BASE1, "Primary basewear color")
    base_color_2: color_property(ColorId.BASE2, "Secondary basewear color")
    inner_color_1: color_property(ColorId.INNER1, "Primary innerwear color")
    inner_color_2: color_property(ColorId.INNER2, "Secondary innerwear color")

    cast_color_1: color_property(ColorId.CAST1, "Cast part color 1")
    cast_color_2: color_property(ColorId.CAST2, "Cast part color 2")
    cast_color_3: color_property(ColorId.CAST3, "Cast part color 3")
    cast_color_4: color_property(ColorId.CAST4, "Cast part color 4")

    main_skin_color: color_property(ColorId.MAIN_SKIN, "Main skin color")
    sub_skin_color: color_property(ColorId.SUB_SKIN, "Sub skin color")
    right_eye_color: color_property(ColorId.RIGHT_EYE, "Right eye color")
    left_eye_color: color_property(ColorId.LEFT_EYE, "Left eye color")
    eyebrow_color: color_property(ColorId.EYEBROW, "Eyebrow color")
    eyelash_color: color_property(ColorId.EYELASH, "Eyelash color")
    hair_color_1: color_property(ColorId.HAIR1, "Primary hair color")
    hair_color_2: color_property(ColorId.HAIR2, "Secondary hair color")

    model_search_categories: bpy.props.EnumProperty(
        name="Model Categories",
        options={"ENUM_FLAG"},
        items=[
            ("COSTUME", "Costumes", "Costumes", "MATCLOTH", 1 << 0),
            ("BASEWEAR", "Basewear", "Basewear", "MATCLOTH", 1 << 1),
            ("OUTERWEAR", "Outerwear", "Outerwear", "MATCLOTH", 1 << 2),
            ("INNERWEAR", "Innerwear", "Innerwear", "TEXTURE", 1 << 3),
            ("BODYPAINT", "Bodypaint", "Bodypaint", "TEXTURE", 1 << 8),
            ("CAST_ARMS", "Cast Arms", "Cast Arms", "MATCLOTH", 1 << 4),
            ("CAST_BODY", "Cast Body", "Cast Body", "MATCLOTH", 1 << 5),
            ("CAST_LEGS", "Cast Legs", "Cast Legs", "MATCLOTH", 1 << 6),
            ("SKIN", "Skin", "Skin", "TEXTURE", 1 << 7),
            ("HAIR", "Hair", "Hair", "USER", 1 << 10),
            ("FACE | FACE_TEXTURE", "Face", "Face", "USER", 1 << 11),
            ("FACEPAINT", "Facepaint", "Facepaint", "USER", 1 << 13),
            ("EARS", "Ears", "Ears", "USER", 1 << 14),
            ("HORNS", "Horns", "Horns", "USER", 1 << 15),
            ("TEETH", "Teeth", "Teeth", "USER", 1 << 16),
            ("EYES", "Eyes", "Eyes", "HIDE_OFF", 1 << 17),
            ("EYEBROWS", "Eyebrows", "Eyebrows", "HIDE_OFF", 1 << 18),
            ("EYELASHES", "Eyelashes", "Eyelashes", "HIDE_OFF", 1 << 19),
            ("STICKER", "Stickers", "Stickers", "TEXTURE", 1 << 9),
            ("ACCESSORY", "Accessories", "Accessories", "MESH_TORUS", 1 << 20),
        ],
        description="Filter by object category",
        default={
            "COSTUME",
            "BASEWEAR",
            "OUTERWEAR",
            "CAST_ARMS",
            "CAST_BODY",
            "CAST_LEGS",
        },
    )

    model_search_versions: bpy.props.EnumProperty(
        name="Model Versions",
        options={"ENUM_FLAG"},
        items=[
            ("NGS", "NGS", "NGS", "", 1 << 0),
            ("CLASSIC", "Classic", "Classic", "", 1 << 1),
        ],
        description="Filter by game version",
        default={"NGS"},
    )

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout
        layout.prop(self, "pso2_data_path")
        layout.prop(self, "debug")

        box = layout.box()
        box.label(text="Import Colors", icon="COLOR")
        grid = box.grid_flow(columns=3)

        for channel in COLOR_CHANNELS.values():
            grid.prop(self, channel.prop)

    def get_pso2_data_path(self):
        return Path(self.pso2_data_path)

    def get_pso2_bin_path(self):
        return self.get_pso2_data_path().parent


def get_preferences(context: bpy.types.Context) -> Pso2ToolsPreferences:
    return context.preferences.addons[__package__].preferences
