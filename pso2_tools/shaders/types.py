from dataclasses import dataclass, field
from typing import Optional

from .. import colors as clr
from .. import material as mat


@dataclass
class ShaderData:
    material: mat.Material
    textures: mat.MaterialTextures
    color_map: Optional[clr.ColorMapping] = field(default_factory=clr.ColorMapping)
    uv_map: Optional[mat.UVMapping] = None
