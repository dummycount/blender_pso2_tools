from pathlib import Path
import os
import re

import bpy
from . import classes
from .shaders import default_colors


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


@classes.register_class
class Pso2ToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    pso2_data_path: bpy.props.StringProperty(
        name="Path to pso2_bin/data",
        subtype="DIR_PATH",
        default=_get_default_data_path(),
    )

    debug: bpy.props.BoolProperty(name="Show debug info", default=False)

    custom_color_1: bpy.props.FloatVectorProperty(
        name="Color 1",
        description="Custom outfit/cast part color 1",
        default=default_colors.BASE_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_2: bpy.props.FloatVectorProperty(
        name="Color 2",
        description="Custom outfit/cast part color 2",
        default=default_colors.BASE_COLOR_2,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_3: bpy.props.FloatVectorProperty(
        name="Color 3",
        description="Custom cast part color 3",
        default=default_colors.BASE_COLOR_3,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    custom_color_4: bpy.props.FloatVectorProperty(
        name="Color 4",
        description="Custom outfit color 4",
        default=default_colors.BASE_COLOR_4,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    inner_color_1: bpy.props.FloatVectorProperty(
        name="Innerwear 1",
        description="Custom innerwear color 1",
        default=default_colors.INNER_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    inner_color_2: bpy.props.FloatVectorProperty(
        name="Innerwear 2",
        description="Custom innerwear color 2",
        default=default_colors.INNER_COLOR_2,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    hair_color_1: bpy.props.FloatVectorProperty(
        name="Hair 1",
        description="Hair color 1",
        default=default_colors.HAIR_COLOR_1,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    hair_color_2: bpy.props.FloatVectorProperty(
        name="Hair 2",
        description="Hair color 2",
        default=default_colors.HAIR_COLOR_2,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    eye_color: bpy.props.FloatVectorProperty(
        name="Eye",
        description="Eye color",
        default=default_colors.EYE_COLOR,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    main_skin_color: bpy.props.FloatVectorProperty(
        name="Skin Main",
        description="Main skin color",
        default=default_colors.MAIN_SKIN_COLOR,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )
    sub_skin_color: bpy.props.FloatVectorProperty(
        name="Skin Sub",
        description="Secondary skin color",
        default=default_colors.SUB_SKIN_COLOR,
        min=0,
        max=1,
        subtype="COLOR",
        size=4,
    )

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout
        layout.prop(self, "pso2_data_path")
        layout.prop(self, "debug")

        box = layout.box()
        box.label(text="Import Colors", icon="COLOR")
        grid = box.grid_flow(columns=3)

        grid.prop(self, "custom_color_1")
        grid.prop(self, "custom_color_2")
        grid.prop(self, "custom_color_3")
        grid.prop(self, "custom_color_4")
        grid.prop(self, "inner_color_1")
        grid.prop(self, "inner_color_2")
        grid.prop(self, "main_skin_color")
        grid.prop(self, "sub_skin_color")
        grid.prop(self, "hair_color_1")
        grid.prop(self, "hair_color_2")
        grid.prop(self, "eye_color")


def get_preferences(context: bpy.types.Context) -> Pso2ToolsPreferences:
    return context.preferences.addons[__package__].preferences
