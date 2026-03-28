#! /usr/bin/env python3
"""
Download wheels for the project's dependencies.
"""

import shutil
import subprocess
from itertools import product
from pathlib import Path

ROOT = Path(__file__).parent.parent
WHEELS = ROOT / "pso2_tools" / "wheels"

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


if __name__ == "__main__":
    main()
