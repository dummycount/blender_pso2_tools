import os

import pythonnet

from .paths import BIN_PATH

_DLL_NAMES = [
    "AquaModelLibrary.Core.dll",
    "AquaModelLibrary.Data.dll",
    "AquaModelLibrary.Helpers.dll",
    "ZamboniLib.dll",
]

_loaded = False


def load():
    global _loaded  # pylint: disable=global-statement
    if _loaded:
        return

    os.add_dll_directory(str(BIN_PATH))
    os.add_dll_directory(str(BIN_PATH / "x64"))

    pythonnet.load("coreclr")

    import clr  # pylint: disable=import-outside-toplevel

    for name in _DLL_NAMES:
        path = str(BIN_PATH / name)
        clr.AddReference(path)  # pylint: disable=no-member # type: ignore

    _loaded = True
