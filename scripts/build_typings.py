#! /usr/bin/env python3
"""
Generate type stubs for .net dependencies.

build_bin.py must be run first.
"""

import shutil
import subprocess
from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent
TYPES_PATH = ROOT_PATH / "typings"
BIN_PATH = ROOT_PATH / "pso2_tools/bin"

DLLS = [
    BIN_PATH / "AquaModelLibrary.Core.dll",
    BIN_PATH / "AquaModelLibrary.Data.dll",
    BIN_PATH / "AquaModelLibrary.Helpers.dll",
    BIN_PATH / "AquaModelLibrary.Native.X64.dll",
    BIN_PATH / "ArchiveLib.dll",
    BIN_PATH / "SharpAssimp.dll",
    BIN_PATH / "NvTriStripDotNet.dll",
    BIN_PATH / "Reloaded.Memory.dll",
    BIN_PATH / "SoulsFormats.dll",
    BIN_PATH / "UnluacNET.dll",
    BIN_PATH / "VrSharp.dll",
    BIN_PATH / "ZamboniLib.dll",
]

STUB_GENERATOR = (
    ROOT_PATH
    / "pythonnet-stub-generator/csharp/PythonNetStubTool"
    / "bin/Release/net9.0/PythonNetStubGenerator.Tool.exe"
)


def main():
    shutil.rmtree(TYPES_PATH, ignore_errors=True)

    subprocess.call([STUB_GENERATOR, "-o", TYPES_PATH, *DLLS])


if __name__ == "__main__":
    main()
