from pprint import pprint

import bpy

from . import preferences


def debug_print(*args, **kwargs):
    if preferences.get_preferences(bpy.context).debug:
        print(*args, **kwargs)


def debug_pprint(*args, **kwargs):
    if preferences.get_preferences(bpy.context).debug:
        pprint(*args, **kwargs)
