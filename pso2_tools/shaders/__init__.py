from typing import Optional, Type

import bpy

from .. import scene_props
from . import (
    builder,
    shader_0100,
    shader_1100,
    shader_1101,
    shader_1102,
    shader_1103,
    shader_1104,
    shader_1105,
    shader_1107,
    shader_1108,
    shader_1109,
    shader_1110,
    shader_1117,
    types,
)


def build_material(
    context: bpy.types.Context,
    material: bpy.types.Material,
    data: types.ShaderData,
):
    if cls := _get_builder(data):
        bld = cls(material, data)
        bld.build(context)

    _update_material_settings(material, data)


def _update_material_settings(material: bpy.types.Material, data: types.ShaderData):
    setattr(material, scene_props.ALPHA_THRESHOLD, data.material.alpha_cutoff)

    if data.material.blend_type in ("add", "blendalpha", "hollow"):
        if data.material.alpha_cutoff > 0:
            material.surface_render_method = "DITHERED"
        else:
            # TODO: use_transparency_overlap looks wrong in some models, such as
            # Twilight Tenzan [Se]. Using DITHERED mode works for those, but then
            # translucent materials look wrong.
            material.surface_render_method = "BLENDED"
            material.use_transparency_overlap = True

    else:
        material.surface_render_method = "BLENDED"
        material.use_transparency_overlap = False

    match data.material.two_sided:
        case 0:
            material.use_backface_culling = True

        case 1:
            material.use_backface_culling = False

        case 2:
            # Not sure about this. Turning on backface culling fixes Z fighting
            # on some opaque models but makes some features of transparent
            # models disappear, so just enable it if not using alpha I guess?
            material.use_backface_culling = data.material.blend_type not in (
                "blendalpha",
                "hollow",
            )


def _get_builder(data: types.ShaderData) -> Optional[Type[builder.ShaderBuilder]]:
    _, vertex = data.material.shaders
    shader_id = int(vertex)

    match shader_id:
        case 100:
            # Classic default
            return shader_0100.Shader0100

        # case 101:
        #     # Classic face
        #     return shader_0101.Shader0101

        case 1100:
            # NGS default
            return shader_1100.Shader1100

        case 1101:
            # NGS horn/teeth
            return shader_1101.Shader1101

        case 1102:
            # NGS skin
            return shader_1102.Shader1102

        case 1103:
            # NGS hair
            return shader_1103.Shader1103

        case 1104:
            # NGS eye
            return shader_1104.Shader1104

        case 1105:
            # NGS eye tear
            return shader_1105.Shader1105

        # case 1106:
        #     # NGS fur?
        #     return shader_1106.Shader1106

        case 1107:
            # NGS eyelash
            return shader_1107.Shader1107

        case 1108:
            # NGS eyebrow
            return shader_1108.Shader1108

        case 1109:
            # NGS ear?
            return shader_1109.Shader1109

        case 1110:
            # NGS default with decal
            return shader_1110.Shader1110

        case 1117:
            # NGS skin with decal
            return shader_1117.Shader1117

        # case 1119:
        #     # NGS unknown (feathers?)
        #     return shader_1119.Shader1119

        # case 1124:
        #     # NGS ear hair?
        #     return shader_1124.Shader1124

        case x if x < 1000:
            return shader_0100.Shader0100

        case _:
            return shader_1100.Shader1100
