from pathlib import Path
import os
import re

import bpy

from . import classes
from .colors import Colors, COLOR_CHANNELS
from .object_category import Category, get_category_enum


PROGRAM_FILES = Path(os.getenv("PROGRAMFILES(x86)"))


def _get_default_data_path() -> str | None:
    win_store = PROGRAM_FILES / "ModifiableWindowsApps/pso2_bin/data"
    if win_store.exists():
        return str(win_store)

    for library in get_steam_libraries():
        steam_path = (
            library / "SteamApps/common/PHANTASYSTARONLINE2_NA_STEAM/pso2_bin/data"
        )
        if steam_path.exists():
            return str(steam_path)

    return ""


def get_steam_libraries() -> list[Path]:
    path_re = re.compile(r'\s*"path"\s*"([^"]+)"\s*')
    steam_libraries_file = PROGRAM_FILES / "Steam/SteamApps/libraryfolders.vdf"
    try:
        with steam_libraries_file.open(encoding="utf-8") as f:
            return [
                Path(match.group(1)) for line in f if (match := path_re.match(line))
            ]
    except OSError:
        return []


def color_property(color: Colors, description: str):
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


@classes.register_class
class Pso2ToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    pso2_data_path: bpy.props.StringProperty(
        name="Path to pso2_bin/data",
        subtype="DIR_PATH",
        default=_get_default_data_path(),
    )

    debug: bpy.props.BoolProperty(name="Show debug info", default=False)

    outer_color_1: color_property(Colors.Outer1, "Primary outerwear color")
    outer_color_2: color_property(Colors.Outer2, "Secondary outerwear color")
    base_color_1: color_property(Colors.Base1, "Primary basewear color")
    base_color_2: color_property(Colors.Base2, "Secondary basewear color")
    inner_color_1: color_property(Colors.Inner1, "Primary innerwear color")
    inner_color_2: color_property(Colors.Inner2, "Secondary innerwear color")

    cast_color_1: color_property(Colors.Cast1, "Cast part color 1")
    cast_color_2: color_property(Colors.Cast2, "Cast part color 2")
    cast_color_3: color_property(Colors.Cast3, "Cast part color 3")
    cast_color_4: color_property(Colors.Cast4, "Cast part color 4")

    main_skin_color: color_property(Colors.MainSkin, "Main skin color")
    sub_skin_color: color_property(Colors.SubSkin, "Sub skin color")
    right_eye_color: color_property(Colors.RightEye, "Right eye color")
    left_eye_color: color_property(Colors.LeftEye, "Left eye color")
    eyebrow_color: color_property(Colors.Eyebrow, "Eyebrow color")
    eyelash_color: color_property(Colors.Eyelash, "Eyelash color")
    hair_color_1: color_property(Colors.Hair1, "Primary hair color")
    hair_color_2: color_property(Colors.Hair2, "Secondary hair color")

    model_search_categories: bpy.props.EnumProperty(
        name="Model Categories",
        options={"ENUM_FLAG"},
        items=(
            get_category_enum(Category.NgsOutfit),
            get_category_enum(Category.NgsCastPart),
            get_category_enum(Category.NgsHeadPart),
            get_category_enum(Category.NgsBodyPaint),
            get_category_enum(Category.Accessory),
            get_category_enum(Category.ClassicOutfit),
            get_category_enum(Category.ClassicCastPart),
            get_category_enum(Category.ClassicHeadPart),
            get_category_enum(Category.ClassicBodyPaint),
            get_category_enum(Category.Sticker),
            get_category_enum(Category.MySpace),
            get_category_enum(Category.Room),
            get_category_enum(Category.NgsMag),
            get_category_enum(Category.ClassicMag),
            get_category_enum(Category.ClassicOther),
            get_category_enum(Category.NgsOther),
            get_category_enum(Category.NgsEnemies),
            get_category_enum(Category.ClassicEnemies),
        ),
        description="Filter by object category",
        default=set(),
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
