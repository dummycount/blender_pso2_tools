import json

import bpy

from .colors import Colors
from .metadata import COLOR_CHANNELS_FILE, update_color_channels
from .object_info import (
    ObjectCategory,
    ObjectInfo,
    ModelPart,
    ObjectType,
)


_colors_updated = False


def ensure_color_channels_updated(context: bpy.types.Context):
    # pylint: disable=global-statement
    global _colors_updated

    if not _colors_updated:
        update_color_channels(context)
        _colors_updated = True


def get_object_color_channels(info: ObjectInfo) -> list[Colors]:
    if colors := _get_object_color_channels(info):
        print(f"Colors for {info.object_id} = {colors}")
        return [Colors(i) for i in colors]

    return []


def _get_object_color_channels(info: ObjectInfo) -> list[int]:
    with COLOR_CHANNELS_FILE.open("r") as f:
        colors: dict[str, dict[str, list[int]]] = json.load(f)

    categories = _get_search_categories(info)
    for category in categories:
        items = colors[category]

        object_id = str(info.object_id)
        if result := items.get(object_id):
            return result

        object_id = object_id[:-1] + "0"
        if result := items.get(object_id):
            return result

    return _get_fallback_colors(info)


def _get_search_categories(info: ObjectInfo):
    if not info.category == ObjectCategory.PLAYER:
        return []

    match info.object_type:
        case ObjectType.NGS_HAIR:
            return ["hair"]

    match info.part:
        case ModelPart.NGS_BASEWEAR:
            return ["basewear", "costume"]

        case ModelPart.NGS_OUTERWEAR:
            return ["outerwear"]

        case ModelPart.NGS_CAST_ARMS:
            return ["castarm"]

        case ModelPart.NGS_CAST_LEGS:
            return ["castleg"]

        case ModelPart.NGS_CAST_BODY:
            return ["costume"]

    return []


def _get_fallback_colors(info: ObjectInfo):
    if not info.category == ObjectCategory.PLAYER:
        return []

    if info.is_outerwear:
        return [Colors.Outer1, Colors.Outer2]

    if info.is_basewear:
        return [Colors.Base1, Colors.Base2]

    if info.is_innerwear:
        return [Colors.Inner1, Colors.Inner2]

    if info.is_cast_part:
        return [Colors.Cast1, Colors.Cast2, Colors.Cast3, Colors.Cast4]

    if info.is_hair:
        return [Colors.Hair1, Colors.Hair2]

    return []
