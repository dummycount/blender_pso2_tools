#! /usr/bin/env python3
"""
Download wheels for the project's dependencies.
"""

import shutil
import subprocess
from itertools import product
from pathlib import Path

import tomlkit

ROOT = Path(__file__).parent.parent
ADDON_PATH = ROOT / "pso2_tools"
WHEELS = ADDON_PATH / "wheels"
MANIFEST = ADDON_PATH / "blender_manifest.toml"

DEPENDENCIES = ["pythonnet==3.0.5", "watchdog==6.0.0"]

PYTHON_VERSIONS = ["3.11", "3.13"]
PLATFORMS = ["win_amd64"]


def main():
    shutil.rmtree(WHEELS, ignore_errors=True)

    for dep, version, platform in product(DEPENDENCIES, PYTHON_VERSIONS, PLATFORMS):
        subprocess.call(
            [
                "pip",
                "download",
                dep,
                "--dest",
                WHEELS,
                "--only-binary=:all:",
                f"--python-version={version}",
                f"--platform={platform}",
            ]
        )

    manifest = tomlkit.parse(MANIFEST.read_text())

    wheels = WHEELS.rglob("*.whl")

    a = tomlkit.array()
    for w in wheels:
        a.add_line(str(w.relative_to(ADDON_PATH).as_posix()), indent="  ")

    a.add_line(indent="")
    manifest["wheels"] = a

    MANIFEST.write_text(tomlkit.dumps(manifest))


if __name__ == "__main__":
    main()
