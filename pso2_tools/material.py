from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional, Tuple
import re
import bpy


Color = Tuple[float, float, float, float]

WHITE: Color = (1, 1, 1, 1)


@dataclass
class CustomColors:
    custom_color1: Optional[Color] = (0.5, 0.5, 0.5, 1.0)
    custom_color2: Optional[Color] = (0.5, 0.5, 0.5, 1.0)
    skin_color: Optional[Color] = (1.0, 0.45, 0.33, 1.0)


def load_textures(folder: Path, pattern="*.png"):
    for texture in folder.rglob(pattern):
        load_image(texture)


def load_image(file: Path) -> bpy.types.Image:
    image = bpy.data.images.load(str(file), check_existing=True)
    name = image.name.removesuffix(".png")

    image.name = name + ".dds"
    image.pack()

    match name.rpartition("_")[2]:
        case "m" | "n" | "o" | "s":
            # Data textures (normal map, etc.)
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = "Non-Color"

    return image


def update_materials(names: Iterable[str], colors: CustomColors = None):
    for name in names:
        update_material(bpy.data.materials[name], colors)


def update_material(mat: bpy.types.Material, colors: CustomColors = None):
    category = Category.from_name(mat.name)
    textures = get_textures(category)

    update_settings(mat)

    tree = mat.node_tree
    bsdf: bpy.types.ShaderNodeBsdfPrincipled = tree.nodes.get("Principled BSDF")
    bsdf.location = [50, 250]
    bsdf.inputs["Metallic"].default_value = 0
    bsdf.inputs["Specular"].default_value = 0

    # Normal map
    normal: bpy.types.ShaderNodeTexImage = tree.nodes.new("ShaderNodeTexImage")
    normal.location = [-1200, -400]
    normal.label = "Normal map texture"
    normal.image = textures.normal

    normal_map: bpy.types.ShaderNodeNormalMap = tree.nodes.get("Normal Map")
    tree.links.new(normal.outputs["Color"], normal_map.inputs["Color"])

    # Diffuse texture + custom colors
    diffuse: bpy.types.ShaderNodeTexImage = tree.nodes.get("Image Texture")
    diffuse.location = [-1200, 200]
    diffuse.label = "Diffuse texture"
    diffuse.image = textures.diffuse

    multi: bpy.types.ShaderNodeTexImage = tree.nodes.new("ShaderNodeTexImage")
    multi.location = [-1200, -100]
    multi.label = "Multi color texture"
    multi.image = textures.multi

    multi_channels: bpy.types.ShaderNodeSeparateRGB = tree.nodes.new(
        "ShaderNodeSeparateRGB"
    )
    multi_channels.location = [-800, -100]

    tree.links.new(multi.outputs["Color"], multi_channels.inputs["Image"])

    colors_group: bpy.types.ShaderNodeGroup = tree.nodes.new("ShaderNodeGroup")
    colors_group.location = [-800, -250]
    colors_group.label = "Colors"
    colors_group.node_tree = get_color_group(category, colors)

    # Not sure what method PSO2 uses for coloring, but "overlay" seems to
    # give reasonable results on most outfits.
    base1: bpy.types.ShaderNodeMixRGB = tree.nodes.new("ShaderNodeMixRGB")
    base1.location = [-350, 200]
    base1.label = "Color 1"
    base1.blend_type = "OVERLAY"
    base1.use_clamp = True

    base2: bpy.types.ShaderNodeMixRGB = tree.nodes.new("ShaderNodeMixRGB")
    base2.location = [-150, 50]
    base2.label = "Color 2"
    base2.blend_type = "OVERLAY"
    base2.use_clamp = True

    tree.links.new(multi_channels.outputs["R"], base1.inputs["Fac"])
    tree.links.new(multi_channels.outputs["G"], base2.inputs["Fac"])
    # TODO: What is blue channel of multi texture? Used in Fubuki tail outfit.
    # TODO: figure out where innerwear color channels come from

    tree.links.new(diffuse.outputs["Color"], base1.inputs["Color1"])
    tree.links.new(base1.outputs["Color"], base2.inputs["Color1"])
    tree.links.new(base2.outputs["Color"], bsdf.inputs["Base Color"])

    tree.links.new(colors_group.outputs[0], base1.inputs["Color2"])
    tree.links.new(colors_group.outputs[1], base2.inputs["Color2"])

    # Apply alpha
    tree.links.new(diffuse.outputs["Alpha"], bsdf.inputs["Alpha"])

    if category == Category.BODY_SKIN:
        # TODO: figure out how to apply innerwear/bodypaint to skin
        base1.blend_type = "MULTIPLY"
        base2.blend_type = "MULTIPLY"


@dataclass
class MaterialTextures:
    diffuse: Optional[bpy.types.Image] = None
    multi: Optional[bpy.types.Image] = None
    specular: Optional[bpy.types.Image] = None  # Is this specular?
    normal: Optional[bpy.types.Image] = None
    mask: Optional[bpy.types.Image] = None

    @staticmethod
    def get(prefix: str, *suffixes: str):
        return MaterialTextures(
            diffuse=find_texture(prefix, suffixes, "d"),
            multi=find_texture(prefix, suffixes, "m"),
            specular=find_texture(prefix, suffixes, "s"),
            normal=find_texture(prefix, suffixes, "n"),
            mask=find_texture(prefix, suffixes, "o"),
        )


def find_texture(
    prefix: str, suffixes: Iterable[str], mat_type: str
) -> Optional[bpy.types.Image]:
    suffixes = "|".join(suffixes)
    pattern = re.compile(rf"^{prefix}_\d+_({suffixes})_{mat_type}\.dds$")
    return next(
        (img for key, img in bpy.data.images.items() if pattern.match(key)),
        None,
    )


MAT_NAME_RE = re.compile(
    r"\((?P<shader>.+)\)\{(?P<mode>.+)\}\[(?P<type>.+)\](?P<name>[^@]+)"
)


class Category(Enum):
    BODY = 0
    BODY_SKIN = 1

    @staticmethod
    def from_name(name: str) -> "Category":
        if m := MAT_NAME_RE.search(name):
            match m.group("shader"):
                case "1100p,1100":
                    return Category.BODY
                case "1102p,1102":
                    return Category.BODY_SKIN

            match m.group("type"):
                case "rbd" | "reboot_bd" | "reboot_pl" | "reboot_player" | "reboot_ba":
                    return Category.BODY

                case "rbd_sk" | "rbd_skin" | "reboot_bd_skin" | "reboot_pl_skin" | "reboot_player_skin" | "reboot_ba_skin" | "reboot_ou_skin":
                    return Category.BODY_SKIN

        return Category.BODY


def get_textures(category: Category) -> MaterialTextures:
    match category:
        case Category.BODY:
            return MaterialTextures.get("pl_rbd", "bw", "bd")

        case Category.BODY_SKIN:
            return MaterialTextures.get("pl_rbd", "sk")

    return MaterialTextures()


def update_settings(mat: bpy.types.Material):
    if m := MAT_NAME_RE.search(mat.name):
        match m.group("mode"):
            case "blendalpha" | "hollow":
                mat.blend_method = "BLEND"
                mat.show_transparent_back = False

            case _:
                mat.blend_method = "OPAQUE"


def get_color_group(category: Category, colors: CustomColors = None):
    colors = colors or CustomColors()
    name = f"PSO2 {category.name.replace('_', ' ').title()}"

    if group := bpy.data.node_groups.get(name, None):
        return group

    group: bpy.types.ShaderNodeTree = bpy.data.node_groups.new(name, "ShaderNodeTree")

    output: bpy.types.NodeGroupOutput = group.nodes.new("NodeGroupOutput")
    output.location = [200, 0]

    base1: bpy.types.ShaderNodeRGB = group.nodes.new("ShaderNodeRGB")
    base1.location = [0, 100]
    base1.label = "Color 1"
    base1.outputs[0].default_value = (
        colors.skin_color if category == Category.BODY_SKIN else colors.custom_color1
    )

    base2: bpy.types.ShaderNodeRGB = group.nodes.new("ShaderNodeRGB")
    base2.location = [0, -100]
    base2.label = "Color 2"
    base2.outputs[0].default_value = (
        WHITE if category == Category.BODY_SKIN else colors.custom_color2
    )

    group.links.new(base1.outputs[0], output.inputs[0])
    group.links.new(base2.outputs[0], output.inputs[1])

    return group
