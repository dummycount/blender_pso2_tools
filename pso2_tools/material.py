import itertools
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

import AquaModelLibrary.Data.PSO2.Aqua.AquaObjectData.Intermediary
import bpy
import System.Numerics

from . import util

Vector4 = tuple[float, float, float, float]


def to_vec4(v: System.Numerics.Vector4) -> Vector4:
    return (float(v.X), float(v.Y), float(v.Z), float(v.W))


@dataclass
class UVMapping:
    from_u_min: float = 0
    from_u_max: float = 1
    to_u_min: float = 0
    to_u_max: float = 1


NGS_CAST_ARMS_UV = UVMapping(from_u_max=1 / 3, to_u_max=2 / 3)
NGS_CAST_BODY_UV = UVMapping(from_u_min=1 / 3, from_u_max=2 / 3, to_u_max=2 / 3)
NGS_CAST_LEGS_UV = UVMapping(from_u_min=2 / 3, to_u_max=2 / 3)

CLASSIC_CAST_ARMS_UV = NGS_CAST_LEGS_UV
CLASSIC_CAST_BODY_UV = NGS_CAST_BODY_UV
CLASSIC_CAST_LEGS_UV = NGS_CAST_ARMS_UV


@dataclass
class Material:
    textures: list[str] = field(default_factory=list)
    uv_sets: list[int] = field(default_factory=list)
    shaders: list[str] = field(default_factory=list)
    blend_type: str = ""
    special_type: str = ""
    name: str = ""
    two_sided: int = 0
    alpha_cutoff: int = 0
    source_alpha: int = 5
    dest_alpha: int = 6

    diffuse_rgba: Vector4 = field(default=(1, 1, 1, 1))
    unknown_rgba_0: Vector4 = field(default=(0.9, 0.9, 0.9, 1))
    srgba: Vector4 = field(default=(0, 0, 0, 1))
    unknown_rgba_1: Vector4 = field(default=(0, 0, 0, 1))

    reserved_0: int = 0
    unknown_float_0: float = 8
    unknown_float_1: float = 1
    unknown_int_0: int = 100
    unknown_int_1: int = 0

    @classmethod
    def from_generic_material(
        cls,
        mat: AquaModelLibrary.Data.PSO2.Aqua.AquaObjectData.Intermediary.GenericMaterial,
    ):
        return cls(  # type: ignore
            textures=[str(x) for x in mat.texNames] if mat.texNames else [],
            uv_sets=[int(x) for x in mat.texUVSets] if mat.texUVSets else [],
            shaders=[str(x) for x in mat.shaderNames] if mat.shaderNames else [],
            blend_type=str(mat.blendType or ""),
            special_type=str(mat.specialType or ""),
            name=str(mat.matName or ""),
            two_sided=int(mat.twoSided),
            alpha_cutoff=int(mat.alphaCutoff),
            source_alpha=int(mat.srcAlpha),
            dest_alpha=int(mat.destAlpha),
            diffuse_rgba=to_vec4(mat.diffuseRGBA),
            unknown_rgba_0=to_vec4(mat.unkRGBA0),
            # pylint: disable-next=protected-access
            srgba=to_vec4(mat._sRGBA),
            unknown_rgba_1=to_vec4(mat.unkRGBA1),
            reserved_0=int(mat.reserve0),
            unknown_float_0=float(mat.unkFloat0),
            unknown_float_1=float(mat.unkFloat1),
            unknown_int_0=int(mat.unkInt0),
            unknown_int_1=int(mat.unkInt1),
        )


@dataclass
class TextureSet:
    alpha: Optional[bpy.types.Image] = None  # a
    diffuse: Optional[bpy.types.Image] = None  # d
    layer: Optional[bpy.types.Image] = None  # l
    mask: Optional[bpy.types.Image] = None  # m
    normal: Optional[bpy.types.Image] = None  # n
    multi: Optional[bpy.types.Image] = None  # s
    env: Optional[bpy.types.Image] = None  # v
    # Not sure what these are yet
    texture_c: Optional[bpy.types.Image] = None
    texture_k: Optional[bpy.types.Image] = None
    texture_g: Optional[bpy.types.Image] = None
    texture_o: Optional[bpy.types.Image] = None
    texture_p: Optional[bpy.types.Image] = None

    def __or__(self, other: "TextureSet"):
        return TextureSet(
            alpha=self.alpha or other.alpha,
            diffuse=self.diffuse or other.diffuse,
            layer=self.layer or other.layer,
            mask=self.mask or other.mask,
            normal=self.normal or other.normal,
            multi=self.multi or other.multi,
            env=self.env or other.env,
            texture_c=self.texture_c or other.texture_c,
            texture_k=self.texture_k or other.texture_k,
            texture_g=self.texture_g or other.texture_g,
            texture_o=self.texture_o or other.texture_o,
            texture_p=self.texture_p or other.texture_p,
        )

    def add(self, tex: bpy.types.Image):
        parts = tex.name.partition(".")[0].split("_")
        if "a" in parts:
            self.alpha = tex
        elif "d" in parts:
            self.diffuse = tex
        elif "l" in parts:
            self.layer = tex
        elif "m" in parts:
            self.mask = tex
        elif "n" in parts:
            self.normal = tex
        elif "s" in parts:
            self.multi = tex
        elif "v" in parts:
            self.env = tex
        elif "c" in parts:
            self.texture_c = tex
        elif "k" in parts:
            self.texture_k = tex
        elif "g" in parts:
            self.texture_g = tex
        elif "o" in parts:
            self.texture_o = tex
        elif "p" in parts:
            self.texture_p = tex


@dataclass
class MaterialTextures:
    default: TextureSet = field(default_factory=TextureSet)
    inner: TextureSet = field(default_factory=TextureSet)
    skin_0: TextureSet = field(default_factory=TextureSet)
    skin_1: TextureSet = field(default_factory=TextureSet)
    decal: TextureSet = field(default_factory=TextureSet)

    def __or__(self, other: "MaterialTextures"):
        return MaterialTextures(
            default=self.default | other.default,
            inner=self.inner | other.inner,
            skin_0=self.skin_0 | other.skin_0,
            skin_1=self.skin_1 | other.skin_1,
            decal=self.decal | other.decal,
        )


FBX_MATERIAL_RE = re.compile(
    r"""^
    \((?P<shaders>[\w,]+)\)
    \{(?P<blend_type>\w+)\}
    (?:\[(?P<special_type>\w+)\])?
    (?P<name>[^@]*)
    (?:@(?P<two_sided>\d+))?
    (?:@(?P<alpha_cutoff>\d+))?
    (?:\..{3}|\(.*\))? # .001 or (1) suffix
    $""",
    re.VERBOSE,
)


def find_material(key: str, materials: Iterable[Material]):
    m = FBX_MATERIAL_RE.match(key)
    if not m:
        return None

    name = m.group("name")
    blend_type = m.group("blend_type")
    special_type = m.group("special_type") or ""
    two_sided = int(m.group("two_sided") or "0")
    alpha_cutoff = int(m.group("alpha_cutoff") or "0")
    shaders = m.group("shaders").split(",")

    def is_match(mat: Material):
        return (
            mat.name == name
            and mat.blend_type == blend_type
            and mat.special_type == special_type
            and mat.two_sided == two_sided
            and mat.alpha_cutoff == alpha_cutoff
            and mat.shaders == shaders
        )

    return next((m for m in materials if is_match(m)), None)


def texture_has_parts(name: str, parts: str | Iterable[str]):
    """
    Get whether a texture name contains all of the given underscore-delimited parts.
    """
    if isinstance(parts, str):
        parts = [parts]

    split_name = name.partition(".")[0].split("_")

    return all(part in split_name for part in parts)


def find_textures(*parts: str, images: Iterable[bpy.types.Image] | None = None):
    images = images or bpy.data.images

    return [img for img in images if texture_has_parts(img.name, parts)]


def find_texture(*parts: str, images: Iterable[bpy.types.Image] | None = None):
    if result := find_textures(*parts, images=images):
        return result[0]
    return None


@dataclass
class ModelMaterials:
    materials: dict[str, Material] = field(default_factory=dict)
    textures: list[bpy.types.Image] = field(default_factory=list)

    # Textures loaded from skin object
    skin_textures: list[bpy.types.Image] = field(default_factory=list)

    # Extra textures loaded from previously-loaded objects
    extra_textures: list[bpy.types.Image] = field(default_factory=list)

    @property
    def is_ngs(self):
        return any(int(m.shaders[1]) >= 1000 for m in self.materials.values())

    @property
    def has_skin_material(self):
        return self.has_material_shader(1102)

    @property
    def has_eye_material(self):
        return self.has_material_shader(1104) or self.has_material_shader(1105)

    @property
    def has_eyelash_material(self):
        return self.has_material_shader(1107)

    @property
    def has_eyebrow_material(self):
        return self.has_material_shader(1108)

    @property
    def has_classic_default_material(self):
        return self.has_material_shader(100)

    @property
    def has_decal_texture(self):
        return self.has_material_texture("pl_body_decal.dds")

    @property
    def has_linked_inner_textures(self):
        return bool(find_textures("rba", images=self.textures))

    def has_material_texture(self, texture_name: str):
        return any(texture_name in m.textures for m in self.materials.values())

    def has_material_shader(self, shader_id: int):
        pixel = f"{shader_id:04d}p"
        vertex = f"{shader_id:04d}"
        return any(m.shaders == [pixel, vertex] for m in self.materials.values())

    def get_textures(self, material: Material):
        result = MaterialTextures()

        for tex in material.textures:
            result |= self._get_texture_set(tex)

        return result

    def _get_texture_by_name(self, name: str):
        candidates = itertools.chain(
            self.textures, self.skin_textures, self.extra_textures
        )
        return next(
            (img for img in candidates if util.remove_blender_suffix(img.name) == name),
            None,
        )

    def _get_texture_set(self, name: str):
        def find(*parts: str, images=None):
            """Get the first texture with the given parts"""
            images = images or self.textures
            return find_texture(*parts, images=images)

        def find_extra(*parts: str):
            """Get the first extra texture with the given parts"""
            return find(*parts, images=self.extra_textures)

        def find_skin(*parts: str, index=0):
            """Get the skin texture with the given parts and index 0 or 1"""
            result = find_textures(*parts, images=self.skin_textures)
            result = sorted(result, key=lambda img: img.name)
            try:
                return result[index]
            except IndexError:
                return None

        def find_alt(alts: Iterable[Iterable[str]], part: str):
            """Equivalent to find(*alts[0], part) or find(*alts[1], part) or ..."""
            for alt in alts:
                if result := find(*alt, part):
                    return result
            return None

        is_ngs = self.is_ngs
        r = MaterialTextures()

        match name:
            # NGS basewear/cast part
            case "pl_body_base_diffuse.dds":
                r.default.diffuse = find_alt(_NGS_BODY_PARTS, "d")
            case "pl_body_base_multi.dds":
                r.default.multi = find_alt(_NGS_BODY_PARTS, "s")
            case "pl_body_base_normal.dds":
                r.default.normal = find_alt(_NGS_BODY_PARTS, "n")
            case "pl_body_base_mask.dds":
                r.default.mask = find("rbd", "bw", "m") or find_alt(
                    _NGS_BODY_PARTS, "l"
                )
            case (
                "pl_body_base_subnormal_01.dds"
                | "pl_body_base_subnormal_02.dds"
                | "pl_body_base_subnormal_03.dds"
            ):
                pass

            # Classic basewear/cast part
            case "pl_body_diffuse.dds":
                r.default.diffuse = find_alt(_CLASSIC_BODY_PARTS, "d")
                r.default.mask = find_alt(_CLASSIC_BODY_PARTS, "m")
                r.default.layer = find_alt(_CLASSIC_BODY_PARTS, "l")
                r.inner.diffuse = find_extra("bd", "iw", "d")
                r.inner.mask = find_extra("bd", "iw", "m")
            case "pl_body_multi.dds":
                r.default.multi = find_alt(_CLASSIC_BODY_PARTS, "s")
                r.inner.multi = find_extra("bd", "iw", "s")
            case "pl_body_normal.dds":
                r.default.normal = find_alt(_CLASSIC_BODY_PARTS, "n")
                r.inner.normal = find_extra("bd", "iw", "n")
            case "pl_body_decal.dds":
                r.decal.diffuse = find_extra("bp", "d")

            # NGS outerwear
            case "pl_body_outer_diffuse.dds":
                r.default.diffuse = find("rbd", "ow", "d")
            case "pl_body_outer_multi.dds":
                r.default.multi = find("rbd", "ow", "s")
            case "pl_body_outer_normal.dds":
                r.default.normal = find("rbd", "ow", "n")
            case "pl_body_outer_mask.dds":
                r.default.mask = find("rbd", "ow", "m")
            case (
                "pl_body_outer_subnormal_01.dds"
                | "pl_body_outer_subnormal_02.dds"
                | "pl_body_outer_subnormal_03.dds"
            ):
                pass

            # NGS skin/innerwear
            case "pl_body_skin_diffuse.dds":
                r.skin_0.diffuse = find_skin("rbd", "sk", "d", index=0)
                r.skin_1.diffuse = find_skin("rbd", "sk", "d", index=1)
                r.inner.diffuse = find("rba", "d") or find_extra("rbd", "iw", "d")
                r.inner.layer = find("rba", "l") or find_extra("rbd", "iw", "l")
            case "pl_body_skin_multi.dds":
                r.skin_0.multi = find_skin("rbd", "sk", "s", index=0)
                r.skin_1.multi = find_skin("rbd", "sk", "s", index=1)
                r.inner.multi = find("rba", "s") or find_extra("rbd", "iw", "s")
            case "pl_body_skin_normal.dds":
                r.skin_0.normal = find_skin("rbd", "sk", "n", index=0)
                r.skin_1.normal = find_skin("rbd", "sk", "n", index=1)
                r.inner.normal = find("rba", "n") or find_extra("rbd", "iw", "n")
            case "pl_body_skin_mask01.dds":
                r.skin_0.mask = find_skin("rbd", "sk", "m", index=0)
                r.skin_1.mask = find_skin("rbd", "sk", "m", index=1)
                r.inner.mask = find("rba", "m") or find_extra("rbd", "iw", "m")
            case (
                "pl_body_skin_subnormal_01.dds"
                | "pl_body_skin_subnormal_02.dds"
                | "pl_body_skin_subnormal_03.dds"
            ):
                pass

            # NGS/classic face
            case "pl_face_diffuse.dds":
                r.default.diffuse = find("rhd", "d") or find("hd", "d")
                if not is_ngs:
                    r.default.mask = find("rhd", "d") or find("hd", "m")
                    r.default.layer = find("rhd", "l") or find("hd", "l")
                    # TODO: no separate materials for eyelashes ("hr", "fa") or
                    # eyebrows ("hb", "fa"). Are these baked into the face texture?
            case "pl_face_multi.dds":
                r.default.multi = find("rhd", "s") or find("hd", "s")
            case "pl_face_normal.dds":
                r.default.normal = find("rhd", "n") or find("hd", "n")
            case "pl_face_mask01.dds":
                r.default.mask = find("rhd", "m")
            case (
                "pl_face_2normal01.dds"
                | "pl_face_2normal02.dds"
                | "pl_face_2normal03.dds"
            ):
                pass

            # NGS eye
            case "pl_leye_diffuse.dds" | "pl_reye_diffuse.dds":
                r.default.diffuse = find_extra("rey", "d")
                r.default.mask = find_extra("rey", "m")
            case "pl_leye_multi.dds" | "pl_reye_multi.dds":
                r.default.multi = find_extra("rey", "s")
            case "pl_leye_normal.dds" | "pl_reye_normal.dds":
                r.default.normal = find_extra("rey", "n")
            case "pl_leye_env.dds" | "pl_reye_env.dds":
                r.default.env = find_extra("rey", "v")

            # Classic eye
            case "pl_eye_diffuse.dds":
                r.default.diffuse = find_extra("ey", "d")
                r.default.mask = find_extra("ey", "m")
            case "pl_eye_multi.dds":
                r.default.multi = find_extra("ey", "s")
            case "pl_eye_env.dds":
                r.default.env = find_extra("ey", "e")  # TODO: is this correct?

            # NGS eyelash
            case "pl_eyelash_diffuse.dds":
                r.default.diffuse = find_extra("res", "d")
            case "pl_eyelash_multi.dds":
                r.default.multi = find_extra("res", "s")
            case "pl_eyelash_normal.dds":
                r.default.normal = find_extra("res", "n")
            case "pl_eyelash_mask.dds":
                r.default.mask = find_extra("res", "m")

            # NGS eyebrow
            case "pl_eyebrow_diffuse.dds":
                r.default.diffuse = find_extra("reb", "d")
            case "pl_eyebrow_multi.dds":
                r.default.multi = find_extra("reb", "s")
            case "pl_eyebrow_normal.dds":
                r.default.normal = find_extra("reb", "n")
            case "pl_eyebrow_mask.dds":
                r.default.mask = find_extra("reb", "m")

            # NGS/classic hair
            case "pl_hair_alpha.dds":
                r.default.alpha = find("rhr", "a")
            case "pl_hair_diffuse.dds":
                r.default.diffuse = find("rhr", "d") or find("hr", "d")
                r.default.mask = find("rhr", "m") or find("hr", "m")
                if not is_ngs:
                    r.default.texture_k = find("hr", "k")
            case "pl_hair_multi.dds" | "pl_hair_specular.dds":
                r.default.multi = find("rhr", "s") or find("hr", "s")
            case "pl_hair_normal.dds":
                r.default.normal = find("rhr", "n") or find("hr", "n")
            case "pl_hair_mask.dds":
                r.default.mask = find("rhr", "m")
            case "pl_hair_noise.dds":
                pass
            case (
                "pl_hair_parts_subnormal_01.dds"
                | "pl_hair_parts_subnormal_02.dds"
                | "pl_hair_parts_subnormal_03.dds"
            ):
                pass

            # NGS ears
            case "pl_ears_diffuse.dds":
                r.default.diffuse = find("rea", "d")
                r.default.mask = find("rea", "m")
            case "pl_ears_multi.dds":
                r.default.multi = find("rea", "s")
            case "pl_ears_normal.dds":
                r.default.normal = find("rea", "n")
            case "pl_ears_mask01.dds":
                r.default.mask = find("rea", "m")
            case (
                "pl_ears_2normal01.dds"
                | "pl_ears_2normal02.dds"
                | "pl_ears_2normal03.dds"
            ):
                pass

            # NGS teeth
            case "pl_dental_diffuse.dds":
                r.default.diffuse = find("rdt", "d")
            case "pl_dental_multi.dds":
                r.default.multi = find("rdt", "s")
            case "pl_dental_normal.dds":
                r.default.normal = find("rdt", "n")
            # TODO: teeth have a mask texture, but it's not used in the material?

            case _:
                if img := self._get_texture_by_name(name):
                    r.default.add(img)

        return r


_NGS_CAST_PARTS = [
    ["rbd", "rm"],  # Cast arms
    ["rbd", "bd"],  # Cast body
    ["rbd", "lg"],  # Cast legs
]

_NGS_BODY_PARTS = [
    ["rbd", "bw"],  # Basewear
    *_NGS_CAST_PARTS,
]

_CLASSIC_BODY_PARTS = [
    ["bd", "bw"],  # Basewear
    ["rm"],  # Cast arms
    ["tr"],  # Cast body
    ["lg"],  # Cast legs
]
