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

    default_muscularity: bpy.props.FloatProperty(
        name="Default Muscularity", min=0, max=1, default=0.5
    )

    default_skin_t1: bpy.props.EnumProperty(
        name="Default T1 Skin Texture",
        items=[
            ("100000", "Base Body T1", ""),
            ("100040", "Base Body T1/B", ""),
            ("100010", "Buff Body", ""),
            ("100020", "Muscular Body", ""),
            ("100030", "Scaly Body T1", ""),
            ("100050", "Tiger Bodysuit T1", ""),
        ],
        default="100000",
    )

    default_skin_t2: bpy.props.EnumProperty(
        name="Default T2 Skin Texture",
        items=[
            ("200000", "Base Body T2", ""),
            ("200010", "Scaly Body T2", ""),
            ("200020", "Tiger Bodysuit T2", ""),
        ],
        default="200000",
    )

    model_search_sort_alpha: bpy.props.BoolProperty(
        name="Sort alphabetical", default=True
    )

    model_search_categories: bpy.props.EnumProperty(
        name="Model Categories",
        options={"ENUM_FLAG"},
        items=[
            # ID strings must match ObjectType enum
            (
                "basewear | costume",
                "Basewear/Setwear",
                "Basewear and setwear",
                "MATCLOTH",
                1 << 0,
            ),
            ("outerwear", "Outerwear", "Outerwear", "MATCLOTH", 1 << 1),
            ("innerwear", "Innerwear", "Innerwear", "TEXTURE", 1 << 2),
            ("bodypaint", "Bodypaint", "Bodypaint", "TEXTURE", 1 << 3),
            ("skin", "Skin", "Skin", "TEXTURE", 1 << 7),
            ("cast_arms", "Cast Arms", "Cast Arms", "MATCLOTH", 1 << 4),
            ("cast_body", "Cast Body", "Cast Body", "MATCLOTH", 1 << 5),
            ("cast_legs", "Cast Legs", "Cast Legs", "MATCLOTH", 1 << 6),
            ("face | face_texture", "Face", "Face", "USER", 1 << 9),
            ("facepaint", "Facepaint", "Facepaint", "USER", 1 << 10),
            ("hair", "Hair", "Hair", "USER", 1 << 8),
            ("ear", "Ears", "Ears", "USER", 1 << 11),
            ("horn", "Horns", "Horns", "USER", 1 << 12),
            ("teeth", "Teeth", "Teeth", "USER", 1 << 13),
            ("sticker", "Stickers", "Stickers", "TEXTURE", 1 << 17),
            ("eye", "Eyes", "Eyes", "HIDE_OFF", 1 << 14),
            ("eyebrow", "Eyebrows", "Eyebrows", "HIDE_OFF", 1 << 15),
            ("eyelash", "Eyelashes", "Eyelashes", "HIDE_OFF", 1 << 16),
            ("accessory", "Accessories", "Accessories", "MESH_TORUS", 1 << 18),
        ],
        description="Filter by object category",
        default={
            "basewear | costume",
            "outerwear",
            "cast_arms",
            "cast_body",
            "cast_legs",
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

    model_search_body_types: bpy.props.EnumProperty(
        name="Body Types",
        options={"ENUM_FLAG"},
        items=[
            ("T1", "T1", "T1 (male)", "", 1 << 0),
            ("T2", "T2", "T2 (female)", "", 1 << 1),
            ("NONE", "None", "Genderless", "", 1 << 2),
        ],
        default={"T1", "T2"},
    )

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "pso2_data_path")
        layout.prop(self, "debug")

        layout.prop(self, "default_muscularity")
        layout.prop(self, "default_skin_t1")
        layout.prop(self, "default_skin_t2")

        box = layout.box()
        box.use_property_split = False
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
