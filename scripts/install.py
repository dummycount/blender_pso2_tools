"""
Build the add-on and install it into Blender.
"""

import argparse
import os
from pathlib import Path
import subprocess

REPO_PATH = Path(__file__).parent.parent


def find_blender():
    # TODO: add handling for multiple installed versions
    program_files = Path(os.getenv("ProgramFiles", "C:/Program Files"))
    blender_root = program_files / "Blender Foundation"
    return next(blender_root.rglob("blender.exe"), None)


def blender(args: list[str], blender_path: Path = None):
    blender_path = blender_path or find_blender()

    if not blender_path:
        raise EnvironmentError("Could not find Blender")

    subprocess.check_call([blender_path, *args], cwd=REPO_PATH)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender-path", "-b", type=Path, help="Path to blender.exe")

    args = parser.parse_args()

    blender(
        ["-b", "--factory-startup", "-P", "scripts/install-blender.py"],
        blender_path=args.blender_path,
    )


if __name__ == "__main__":
    main()
