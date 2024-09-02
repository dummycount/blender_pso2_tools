import bpy

from .colors import COLOR_CHANNELS
from .preferences import get_preferences

HIDE_INNERWEAR = "pso2_hide_innerwear"
MUSCULARITY = "pso2_muscularity"


def add_scene_properties(context: bpy.types.Context):
    preferences = get_preferences(context)

    setattr(
        bpy.types.Scene,
        HIDE_INNERWEAR,
        bpy.props.BoolProperty(name="Hide Innerwear", default=False),
    )

    setattr(
        bpy.types.Scene,
        MUSCULARITY,
        bpy.props.FloatProperty(
            name="Muscularity",
            min=0,
            max=1,
            default=preferences.default_muscularity,
            subtype="FACTOR",
        ),
    )

    for channel in COLOR_CHANNELS.values():
        name = channel.custom_property_name
        setattr(
            bpy.types.Scene,
            name,
            bpy.props.FloatVectorProperty(
                name=channel.name,
                subtype="COLOR",
                default=getattr(preferences, channel.prop),
                min=0,
                max=1,
                size=4,
            ),
        )
