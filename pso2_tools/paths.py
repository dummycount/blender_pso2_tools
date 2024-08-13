from pathlib import Path

import bpy

ADDON_PATH = Path(__file__).parent
BIN_PATH = ADDON_PATH / "bin"


def get_data_path():
    return Path(bpy.utils.extension_path_user(__package__, create=True))
