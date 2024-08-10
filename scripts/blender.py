"""
Find and run Blender.
"""

import os
from pathlib import Path
import subprocess
import sys


def find_blender() -> Path:
    # TODO: add handling for multiple installed versions
    program_files = Path(os.getenv("ProgramFiles", "C:/Program Files"))
    blender_root = program_files / "Blender Foundation"
    try:
        return next(blender_root.rglob("blender.exe"))
    except StopIteration as ex:
        raise RuntimeError("Could not find Blender") from ex


def main():
    blender = find_blender()
    subprocess.call([blender] + sys.argv[1:])


if __name__ == "__main__":
    main()
