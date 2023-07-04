"""
Script to run in Blender's Python environment to build and install the add-on.
"""

import ensurepip
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from urllib.request import urlopen

import bpy

SCRIPT_DIR = Path(__file__).parent

PREFIX_PATH = SCRIPT_DIR / "src/Python"
PYTHON_LIBS_PATH = PREFIX_PATH / "libs"
PYTHON_INCLUDE_PATH = PREFIX_PATH / "Include"

VSWHERE_PATH = Path(
    f"{os.getenv('ProgramFiles(x86)')}/Microsoft Visual Studio/Installer/vswhere.exe"
)


def get_vsdevcmd():
    command = [VSWHERE_PATH, "-latest", "-property", "installationPath"]
    install_path = subprocess.check_output(command, text=True).strip()
    return Path(install_path) / "Common7/Tools/VsDevCmd.bat"


def link_addon():
    user_path = Path(bpy.utils.resource_path("USER"))

    source = SCRIPT_DIR / "pso2_tools"
    target = user_path / "scripts" / "addons" / "pso2_tools"

    if not target.exists():
        print(f"Linking {source.name} to {target}")

        target.parent.mkdir(exist_ok=True, parents=True)
        os.symlink(source, target, target_is_directory=True)


def get_source_members(tar: tarfile.TarFile, subdir: str, pyconfig: str):
    subdir_len = len(subdir)
    for member in tar.getmembers():
        if member.path.startswith(subdir):
            member.path = member.path[subdir_len:]
            yield member

    member = tar.getmember(pyconfig)
    member.path = "pyconfig.h"
    yield member


def fetch_python_source():
    """
    Fetch Python source files which are needed to build native code extensions
    but not included with Blender.
    """
    version_info = sys.version_info
    version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    url = f"https://www.python.org/ftp/python/{version}/Python-{version}.tgz"

    print(f"Downloading {url}")

    with urlopen(url) as response:
        file = BytesIO(response.read())

        with tarfile.open(fileobj=file, mode="r:gz") as tar:
            subdir = f"Python-{version}/Include/"
            pyconfig = f"Python-{version}/PC/pyconfig.h"

            tar.extractall(
                members=get_source_members(tar, subdir, pyconfig),
                path=PYTHON_INCLUDE_PATH,
            )


def get_dll_exports(vsdevcmd: Path, lib_path: Path):
    command = f'cmd /c " "{vsdevcmd}" && dumpbin /exports "{lib_path}" "'
    output = subprocess.check_output(command, text=True)

    found_table = False

    for line in output.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("ordinal"):
            found_table = True
            continue

        if not found_table:
            continue

        if line.startswith("Summary"):
            break

        _, _, _, name = line.split()
        yield name


def build_python_lib():
    """
    Build the .lib file needed to link native code extensions by reverse
    engineering it from the Python .dll file included with Blender.
    """
    vsdevcmd = get_vsdevcmd()

    lib_path = next(Path(sys.executable).parent.glob("*.dll"))

    def_path = PYTHON_LIBS_PATH / lib_path.with_suffix(".def").name
    lib_path = def_path.with_suffix(".lib")

    def_path.parent.mkdir(parents=True, exist_ok=True)

    with def_path.open("w", encoding="utf-8") as f:
        print(f"LIBRARY {lib_path.with_suffix('').name}", file=f)
        print("EXPORTS", file=f)

        for export in get_dll_exports(vsdevcmd, lib_path):
            print(f"   {export}", file=f)

    # TODO: currently assuming 64-bit. Check for 32 and use /machine:x86 if needed.
    subprocess.check_call(
        f'cmd /c " "{vsdevcmd}" && lib "/def:{def_path}" "/out:{lib_path}" /machine:x64"'
    )


if not PYTHON_INCLUDE_PATH.exists():
    fetch_python_source()

if not PYTHON_LIBS_PATH.exists():
    build_python_lib()

ensurepip.bootstrap()

subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "pip"])
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-e", "."],
    env={
        **os.environ,
        "CFLAGS": f'"-I{PYTHON_INCLUDE_PATH}"',
        "LDFLAGS": f'"/LIBPATH:{PYTHON_LIBS_PATH}"',
    },
)

link_addon()
