"""
Download wheels for the project's dependencies.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
WHEELS = ROOT / "pso2_tools" / "wheels"

DEPENDENCIES = ["pythonnet~=3.0.3", "watchdog~=5.0.0"]

PYTHON_VERSION = "3.11"
PLATFORM = "win_amd64"


def main():
    for dep in DEPENDENCIES:
        subprocess.call(
            [
                "pip",
                "download",
                dep,
                "--dest",
                WHEELS,
                "--only-binary=:all:",
                f"--python-version={PYTHON_VERSION}",
                f"--platform={PLATFORM}",
            ]
        )


if __name__ == "__main__":
    main()
