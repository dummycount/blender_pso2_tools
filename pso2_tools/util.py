import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    import bpy.stub_internal
    import System.Collections.Generic

    OperatorResult = set[bpy.stub_internal.rna_enums.OperatorReturnItems]
    BlenderIcon = bpy.stub_internal.rna_enums.IconItems
else:
    OperatorResult = set[str]
    BlenderIcon = str


K = TypeVar("K")
T = TypeVar("T")


def dict_get(d: "System.Collections.Generic.Dictionary_2[K, T]", key: K) -> T | None:
    from System.Collections.Generic import KeyNotFoundException

    try:
        return d[key]
    except KeyNotFoundException:  # type: ignore
        return None


F = TypeVar("F", bound=Callable[..., Any])


class copy_signature(Generic[F]):
    def __init__(self, target: F) -> None: ...
    def __call__(self, wrapped: Callable[..., Any]) -> F:
        return wrapped  # type: ignore


BLENDER_SUFFIX_RE = re.compile(r"\.\d+$")


def remove_blender_suffix(name: str):
    return BLENDER_SUFFIX_RE.sub("", name)
