"""
Script to run in Blender's Python environment to build and install the add-on.

Do not run this directly. Run install.py instead.
"""

import ensurepip
import os
from pathlib import Path
import subprocess
import sys

import bpy

REPO_PATH = Path(__file__).parent.parent

VSWHERE_PATH = Path(
    f"{os.getenv('ProgramFiles(x86)')}/Microsoft Visual Studio/Installer/vswhere.exe"
)


def get_vsdevcmd():
    command = [VSWHERE_PATH, "-latest", "-property", "installationPath"]
    install_path = subprocess.check_output(command, text=True).strip()
    return Path(install_path) / "Common7/Tools/VsDevCmd.bat"


def link_addon():
    user_path = Path(bpy.utils.resource_path("USER"))

    source = REPO_PATH / "pso2_tools"
    target = user_path / "scripts" / "addons" / "pso2_tools"

    if not target.exists():
        print(f"Linking {source.name} to {target}")

        target.parent.mkdir(exist_ok=True, parents=True)
        os.symlink(source, target, target_is_directory=True)


ensurepip.bootstrap()

subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "pip"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])

link_addon()
