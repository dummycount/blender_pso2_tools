"""
Builds dependencies.
"""

import argparse
import os
from pathlib import Path
import subprocess

REPO_PATH = Path(__file__).parent.parent
ADDON_PATH = REPO_PATH / "pso2_tools"
CLI_PATH = REPO_PATH / "Pso2Cli"

BIN_SOURCE = CLI_PATH / "Release" / "Pso2Cli"
BIN_TARGET = ADDON_PATH / "bin"


def build():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", "-c", action="store_true")

    args = parser.parse_args()

    command = ["pwsh", CLI_PATH / "BuildRelease.ps1"]
    if args.clean:
        command.append("-Clean")

    subprocess.check_call(command, cwd=CLI_PATH)

    if not BIN_TARGET.exists():
        os.symlink(BIN_SOURCE, BIN_TARGET, target_is_directory=True)


if __name__ == "__main__":
    build()
