from ..colors import ColorId, ColorMapping
from . import shader_1100


class Shader1107(shader_1100.Shader1100):
    """NGS eyelash shader"""

    @property
    def colors(self):
        return ColorMapping(red=ColorId.EYELASH)

    @property
    def uv_map(self):
        return None
