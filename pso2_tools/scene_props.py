import bpy

from .colors import COLOR_CHANNELS
from .preferences import get_preferences

# Scene
HIDE_INNERWEAR = "pso2_hide_innerwear"
MUSCULARITY = "pso2_muscularity"

# Object
ALPHA_THRESHOLD = "pso2_alpha_threshold"


def add_scene_properties():
    preferences = get_preferences(bpy.context)

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


def add_material_properties():
    setattr(
        bpy.types.Material,
        ALPHA_THRESHOLD,
        bpy.props.IntProperty(
            name="Alpha Threshold",
            min=0,
            max=255,
            default=0,
            subtype="FACTOR",
        ),
    )
