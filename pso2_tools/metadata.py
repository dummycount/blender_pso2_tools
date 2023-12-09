from pathlib import Path
import shutil

import bpy

from .convert import make_color_channels, make_file_lists
from .preferences import get_preferences


DATA_DIR = Path(__file__).parent / "data"
FILE_LIST_DIR = DATA_DIR / "FileLists"
COLOR_CHANNELS_FILE = DATA_DIR / "ColorChannels.json"


def update_color_channels(context: bpy.types.Context):
    pso2_bin = get_preferences(context).get_pso2_bin_path()
    make_color_channels(pso2_bin, COLOR_CHANNELS_FILE)


def update_file_lists(context: bpy.types.Context):
    shutil.rmtree(FILE_LIST_DIR, ignore_errors=True)

    pso2_bin = get_preferences(context).get_pso2_bin_path()
    make_file_lists(pso2_bin, FILE_LIST_DIR)
