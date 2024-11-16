# pylint: disable=import-outside-toplevel

import pythonnet

from .paths import BIN_PATH

_DLL_NAMES = [
    "AssimpNet.dll",
    "AquaModelLibrary.Core.dll",
    "AquaModelLibrary.Data.dll",
    "AquaModelLibrary.Helpers.dll",
    "ZamboniLib.dll",
]

_PROBING_PATH_X64 = str(BIN_PATH / "x64")

_loaded = False


def load():
    global _loaded  # pylint: disable=global-statement
    if _loaded:
        return

    pythonnet.load("coreclr")

    import clr

    for name in _DLL_NAMES:
        path = str(BIN_PATH / name)
        clr.AddReference(path)  # pylint: disable=no-member # type: ignore

    from Assimp.Unmanaged import AssimpLibrary  # type: ignore

    AssimpLibrary.Instance.Resolver.SetProbingPaths64(_PROBING_PATH_X64)

    _loaded = True
