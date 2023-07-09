from dataclasses import dataclass, field
import json
import re
import textwrap

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


@dataclass
class AqpMaterial:
    name: str = ""
    blend_type: str = ""
    special_type: str = ""
    two_sided: int = 0
    alpha_cutoff: int = 0
    textures: list[str] = field(default_factory=list)
    shaders: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict):
        return AqpMaterial(**d)

    @staticmethod
    def from_fbx_name(name: str):
        if match := FBX_MATERIAL_RE.match(name):
            return AqpMaterial(
                name=match.group("name"),
                blend_type=match.group("blend_type"),
                special_type=match.group("special_type") or "",
                two_sided=int(match.group("two_sided") or "0"),
                alpha_cutoff=int(match.group("alpha_cutoff") or "0"),
                shaders=match.group("shaders").split(","),
            )

        raise ValueError(
            textwrap.dedent(
                f"""\
                Invalid material name "{name}".
                Name must be of the format:

                (shader0,shader1){{blend_type}}[special_type]name@two_sided@clip_threshold

                (shader0,shader1) -- shader names, e.g. (1100p,1100)
                {{blend_type}}      -- {{opaque}}, {{blendalpha}}, {{hollow}}, or {{add}}
                [special_type]    -- (optional) [rbd], [rbd_sk], etc...
                name              -- the PSO2 material name
                @two_sided        -- (optional) 0 = backface culling, 1 = no backface culling
                @clip_threshold   -- (optional) alpha clip threshold (0-255)"""
            )
        )

    @property
    def fbx_name(self):
        special_type = f"[{self.special_type}]" if self.special_type else ""
        return f"({'.'.join(self.shaders)}){{{self.blend_type}}}{special_type}{self.name}@{self.two_sided}@{self.alpha_cutoff}"

    def is_match(self, other: "AqpMaterial"):
        return (
            self.is_loose_match(other)
            and self.two_sided == other.two_sided
            and self.alpha_cutoff == other.alpha_cutoff
        )

    def is_loose_match(self, other: "AqpMaterial"):
        return (
            self.name.lower() == other.name.lower()
            and self.blend_type == other.blend_type
            and self.special_type == other.special_type
            and self.shaders == other.shaders
        )


@dataclass
class AqpInfo:
    materials: list[AqpMaterial] = field(default_factory=list)

    @staticmethod
    def from_json(data: str):
        return AqpInfo.from_dict(json.loads(data))

    @staticmethod
    def from_dict(d: dict):
        return AqpInfo(
            materials=[AqpMaterial.from_dict(value) for value in d.get("materials")]
        )

    def get_fbx_material(self, fbx_name: str):
        try:
            material = AqpMaterial.from_fbx_name(fbx_name)
        except ValueError as ex:
            print(ex)
            return None

        if result := next(
            (other for other in self.materials if material.is_match(other)), None
        ):
            return result

        return next(
            (other for other in self.materials if material.is_loose_match(other)), None
        )
