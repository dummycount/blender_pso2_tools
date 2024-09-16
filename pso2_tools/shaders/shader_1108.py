from ..colors import ColorId, ColorMapping
from . import shader_1100


class Shader1108(shader_1100.Shader1100):
    """NGS eyebrow shader"""

    @property
    def colors(self):
        return ColorMapping(red=ColorId.EYEBROW)

    @property
    def uv_map(self):
        return None
