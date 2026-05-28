from pathlib import Path

import clr_loader
import pythonnet

from .paths import BIN_PATH

_DLL_NAMES = [
    "AquaModelLibrary.Core.dll",
    "AquaModelLibrary.Data.dll",
    "AquaModelLibrary.Helpers.dll",
    "SharpAssimp.dll",
    "ZamboniLib.dll",
]

_PROBING_PATH_X64 = str(BIN_PATH / "x64")

_DOTNET_ROOT = Path("C:/Program Files/dotnet")

_loaded = False
_probing_paths_set = False


def load():
    global _loaded
    if _loaded:
        return

    if _DOTNET_ROOT.exists():
        rt = clr_loader.get_coreclr(dotnet_root=_DOTNET_ROOT)
        pythonnet.load(rt)
    else:
        pythonnet.load("coreclr")

    import clr

    for name in _DLL_NAMES:
        path = str(BIN_PATH / name)
        clr.AddReference(path)  # type: ignore

    _loaded = True


def set_assimp_probing_paths():
    global _probing_paths_set
    if _probing_paths_set:
        return

    from SharpAssimp.Unmanaged import AssimpLibrary

    AssimpLibrary.Instance.Resolver.SetProbingPaths64([_PROBING_PATH_X64])

    _probing_paths_set = True
