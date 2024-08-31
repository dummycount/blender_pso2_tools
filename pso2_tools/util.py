import re
from contextlib import contextmanager
from typing import Any, Optional

from System.Collections.Generic import KeyNotFoundException


def dict_get(d, key: Any) -> Optional[Any]:
    try:
        return d[key]
    except KeyNotFoundException:
        return None


BLENDER_SUFFIX_RE = re.compile("\.\d+$")


def remove_blender_suffix(name: str):
    return BLENDER_SUFFIX_RE.sub("", name)
