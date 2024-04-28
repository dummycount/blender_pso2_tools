"""
Script to run in Blender's Python environment to build and install the add-on.

Do not run this directly. Run install.py instead.
"""

import ensurepip
from io import BytesIO
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
from urllib.request import urlopen

import bpy

REPO_PATH = Path(__file__).parent.parent

PREFIX_PATH = REPO_PATH / "src/Python"
PYTHON_LIBS_PATH = PREFIX_PATH / "libs"
PYTHON_INCLUDE_PATH = PREFIX_PATH / "Include"
PYTHON_VERSION_FILE = PREFIX_PATH / "version.txt"

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


def get_dll_exports(vsdevcmd: Path, dll_path: Path):
    command = f'cmd /c " "{vsdevcmd}" && dumpbin /exports "{dll_path}" "'
    output = subprocess.check_output(command, text=True)

    table_re = re.compile(r"(\d+)\s+([0-9A-F]+)\s+(?:([0-9A-F]+)\s+)?(\w+)")

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

        m = table_re.search(line)
        if m:
            yield m.group(4)


def build_python_lib():
    """
    Build the .lib file needed to link native code extensions by reverse
    engineering it from the Python .dll file included with Blender.
    """
    vsdevcmd = get_vsdevcmd()

    dll_path = next(Path(sys.executable).parent.glob("*.dll"))

    def_path = PYTHON_LIBS_PATH / dll_path.with_suffix(".def").name
    lib_path = def_path.with_suffix(".lib")

    def_path.parent.mkdir(parents=True, exist_ok=True)

    with def_path.open("w", encoding="utf-8") as f:
        print(f"LIBRARY {dll_path.with_suffix('').name}", file=f)
        print("EXPORTS", file=f)

        for export in get_dll_exports(vsdevcmd, dll_path):
            print(f"   {export}", file=f)

    # TODO: currently assuming 64-bit. Check for 32 and use /machine:x86 if needed.
    subprocess.check_call(
        f'cmd /c " "{vsdevcmd}" && lib "/def:{def_path}" "/out:{lib_path}" /machine:x64"'
    )


def setup_python_dependencies():
    try:
        version = PYTHON_VERSION_FILE.read_text()
        if version != sys.version:
            print("Dependencies version mismatch. Rebuilding.")
            shutil.rmtree(PREFIX_PATH)
    except FileNotFoundError:
        if PREFIX_PATH.exists():
            print("Dependencies version missing. Rebuilding.")
            shutil.rmtree(PREFIX_PATH)

    if not PYTHON_INCLUDE_PATH.exists():
        fetch_python_source()

    if not PYTHON_LIBS_PATH.exists():
        build_python_lib()

    PYTHON_VERSION_FILE.write_text(sys.version)


setup_python_dependencies()
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
