"""
Generate type stubs for .net dependencies.

build_bin.py must be run first.
"""

from pathlib import Path
import shutil
import subprocess

ROOT_PATH = Path(__file__).parent.parent
TYPES_PATH = ROOT_PATH / "typings"
BIN_PATH = ROOT_PATH / "pso2_tools/bin"

DLLS = [
    BIN_PATH / "ZamboniLib.dll",
    BIN_PATH / "AquaModelLibrary.Core.dll",
    BIN_PATH / "AquaModelLibrary.Data.dll",
    BIN_PATH / "AquaModelLibrary.Helpers.dll",
    BIN_PATH / "AquaModelLibrary.Native.X64.dll",
]


def main():
    if not shutil.which("GeneratePythonNetStubs"):
        print("Run the following command to install GeneratePythonNetStubs:")
        print("dotnet tool install --global pythonnetstubgenerator.tool")
        return

    for dll in DLLS:
        subprocess.call(
            ["GeneratePythonNetStubs", "--dest-path", TYPES_PATH, "--target-dlls", dll]
        )


if __name__ == "__main__":
    main()
