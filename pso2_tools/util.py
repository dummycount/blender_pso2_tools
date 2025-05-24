import re
from typing import TypeVar

import System.Collections.Generic

K = TypeVar("K")
T = TypeVar("T")


def dict_get(d: "System.Collections.Generic.Dictionary_2[K, T]", key: K) -> T | None:
    try:
        return d[key]  # type: ignore
    except System.Collections.Generic.KeyNotFoundException:  # type: ignore
        return None


BLENDER_SUFFIX_RE = re.compile(r"\.\d+$")


def remove_blender_suffix(name: str):
    return BLENDER_SUFFIX_RE.sub("", name)
