import bpy

from . import shader_1100, shader_1101, shader_1102, shader_1103, types


def build_material(
    context: bpy.types.Context,
    material: bpy.types.Material,
    data: types.ShaderData,
):
    if builder := _get_builder(material, data):
        builder.build(context)

    _update_material_settings(material, data)


def _update_material_settings(material: bpy.types.Material, data: types.ShaderData):
    if data.material.blend_type in ("add", "blendalpha", "hollow"):
        if data.material.alpha_cutoff > 0:
            material.blend_method = "CLIP"
            material.alpha_threshold = data.material.alpha_cutoff / 256
        else:
            material.blend_method = "BLEND"  # TODO: HASHED looks better on hair?
            material.show_transparent_back = False
    else:
        material.blend_method = "OPAQUE"

    match data.material.two_sided:
        case 0:
            material.use_backface_culling = True

        case 1:
            material.use_backface_culling = False

        case 2:
            # Not sure about this. Turning on backface culling fixes Z fighting
            # on some opaque models but makes some features of transparent
            # models disappear, so just enable it if not using alpha.
            material.use_backface_culling = material.blend_method != "blendalpha"


def _get_builder(material: bpy.types.Material, data: types.ShaderData):
    _, vertex = data.material.shaders
    shader_id = int(vertex)

    match shader_id:
        case 1100:
            # NGS default
            return shader_1100.Shader1100(material, data)

        case 1101:
            # NGS horn/teeth
            return shader_1101.Shader1101(material, data)

        case 1102:
            # NGS skin
            return shader_1102.Shader1102(material, data)

        case 1103:
            # NGS hair
            return shader_1103.Shader1103(material, data)

        case _:
            return shader_1100.Shader1100(material, data)
