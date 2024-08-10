"""
Build or validate the extension.
"""

import argparse
from pathlib import Path
import subprocess

from blender import find_blender

ROOT_PATH = Path(__file__).parent.parent
SRC_PATH = ROOT_PATH / "pso2_tools"
DEST_PATH = ROOT_PATH / "dist"


def validate(blender_path: Path):
    subprocess.call([blender_path, "-c", "extension", "validate", SRC_PATH])


def build(blender_path: Path):
    DEST_PATH.mkdir(parents=True, exist_ok=True)

    subprocess.call(
        [
            blender_path,
            "-c",
            "extension",
            "build",
            "--source-dir",
            SRC_PATH,
            "--output-dir",
            DEST_PATH,
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender-path", "-b", type=Path, help="Path to blender.exe")
    parser.add_argument(
        "command",
        choices=(
            "build",
            "validate",
        ),
    )

    args = parser.parse_args()

    blender_path: Path = args.blender_path or find_blender()

    match args.command:
        case "build":
            build(blender_path)

        case "validate":
            validate(blender_path)


if __name__ == "__main__":
    main()
