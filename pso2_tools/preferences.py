from pathlib import Path
import os
import re

from bpy.types import AddonPreferences, Context
from bpy.props import StringProperty
from . import classes


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
    except:
        return []


@classes.register_class
class Pso2ToolsPreferences(AddonPreferences):
    bl_idname = __package__

    pso2_data_path: StringProperty(
        name="Path to pso2_bin/data",
        subtype="DIR_PATH",
        default=_get_default_data_path(),
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "pso2_data_path")


def get_preferences(context: Context) -> Pso2ToolsPreferences:
    return context.preferences.addons[__package__].preferences
