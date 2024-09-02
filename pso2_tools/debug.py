from pprint import pprint

import bpy

from .preferences import get_preferences


def debug_print(*args, **kwargs):
    if get_preferences(bpy.context).debug:
        print(*args, **kwargs)


def debug_pprint(*args, **kwargs):
    if get_preferences(bpy.context).debug:
        pprint(*args, **kwargs)
