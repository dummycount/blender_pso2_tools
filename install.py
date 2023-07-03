"""
Build the add-on and install it into Blender.
"""

import os
from pathlib import Path
import subprocess


def find_blender():
    # TODO: add handling for multiple installed versions
    program_files = Path(os.getenv("ProgramFiles", "C:/Program Files"))
    blender_root = program_files / "Blender Foundation"
    return next(blender_root.rglob("blender.exe"), None)


def blender(*args: list[str]):
    blender_path = find_blender()

    if not blender_path:
        raise EnvironmentError("Could not find Blender")

    subprocess.check_call([blender_path, *args])


def main():
    blender("-b", "-P", "install-blender.py")


if __name__ == "__main__":
    main()
