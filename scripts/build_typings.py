"""
Generate type stubs for .net dependencies.

build_bin.py must be run first.
"""

import shutil
import subprocess
from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent
TYPES_PATH = ROOT_PATH / "typings"
EXTRA_STUBS_PATH = ROOT_PATH / "stubs"
BIN_PATH = ROOT_PATH / "pso2_tools/bin"

DLLS = [
    BIN_PATH / "AssimpNet.dll",
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

    shutil.rmtree(TYPES_PATH)

    for dll in DLLS:
        subprocess.call(
            ["GeneratePythonNetStubs", "--dest-path", TYPES_PATH, "--target-dlls", dll]
        )

    # Workaround for https://github.com/MHDante/pythonnet-stub-generator/issues/6
    # Append manually written type stubs
    for extra in EXTRA_STUBS_PATH.rglob("*.pyi"):
        dest_path = TYPES_PATH / extra.relative_to(EXTRA_STUBS_PATH)

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if dest_path.is_file():
            dest_path.write_text(dest_path.read_text() + "\n" + extra.read_text())
        else:
            shutil.copy(extra, dest_path)


if __name__ == "__main__":
    main()
