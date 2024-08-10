"""
Build .net dependencies.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).parent.parent

FRAMEWORK = "net6.0"

FBX_URL = "https://www.autodesk.com/content/dam/autodesk/www/adn/fbx/2020-1/fbx20201_fbxsdk_vs2017_win.exe"
NUGET_URL = "https://learn.microsoft.com/en-us/nuget/consume-packages/install-use-packages-nuget-cli"
VISUAL_STUDIO_URL = "https://visualstudio.microsoft.com/vs/community/"

VSWHERE = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")

FBX_TARGET = Path("C:/Program Files/Autodesk/FBX/FBX SDK/2020.1")
FBX_PATH = ROOT / "PSO2-Aqua-Library/AquaModelLibrary.Native/Dependencies/FBX"
BIN_PATH = ROOT / "pso2_tools/bin"

AQUA_SLN = ROOT / "PSO2-Aqua-Library/AquaModelLibrary.sln"
AQUA_CORE_PATH = ROOT / "PSO2-Aqua-Library/AquaModelLibrary.Core"

PACKAGES_PATH = ROOT / "packages"
PACKAGES = [
    ("AssimpNet", "5.0.0-beta1"),
    ("Reloaded.Memory", "9.3.2"),
]


def check_dependencies():
    if not shutil.which("nuget"):
        print(f"Please install nuget: {NUGET_URL}")

    if not VSWHERE.exists():
        print(f"Please install Visual Studio: {VISUAL_STUDIO_URL}")
        sys.exit(1)

    if not FBX_TARGET.exists():
        print(f"Please install FBX SDK 2020.1: {FBX_URL}")
        sys.exit(1)


def make_symlink(path: Path, target: Path):
    if path.is_symlink():
        if path.readlink() == target:
            # Already symlinked to the correct thing.
            return
        path.unlink()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target, target_is_directory=target.is_dir())


def install_packages():
    for package, version in PACKAGES:
        subprocess.check_call(
            [
                "nuget",
                "install",
                package,
                "-Version",
                version,
                "-Framework",
                FRAMEWORK,
                "-OutputDirectory",
                PACKAGES_PATH,
            ]
        )


def copy_package_dlls():
    frameworks = [FRAMEWORK, "netstandard1.3"]

    for package, version in PACKAGES:
        src = PACKAGES_PATH / f"{package}.{version}/lib"
        src = next(src / f for f in frameworks if (src / f).exists())

        for dll in src.glob("*.dll"):
            shutil.copyfile(dll, BIN_PATH / dll.name)


def call_msbuild(args: list[str]):
    vs = json.loads(
        subprocess.check_output(
            [VSWHERE, "-latest", "-format", "json"], encoding="utf-8"
        )
    )
    msbuild = Path(vs[0]["installationPath"]) / "Msbuild/Current/Bin/MSBuild.exe"

    subprocess.check_call([msbuild, *args])


def main():
    check_dependencies()

    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()
    target = "Rebuild" if args.clean else "Build"
    config = "Debug" if args.debug else "Release"

    # Set up Aqua Library dependencies
    make_symlink(FBX_PATH / "lib", FBX_TARGET / "lib")
    make_symlink(FBX_PATH / "include", FBX_TARGET / "include")

    install_packages()

    # Build Aqua Library
    call_msbuild(
        [
            AQUA_SLN,
            "-p:RestorePackagesConfig=true",
            f"-p:Configuration={config}",
            f"-t:{target}",
            "-verbosity:minimal",
            "-restore",
        ]
    )

    # Copy to pso2_tools/bin folder
    out_path = AQUA_CORE_PATH / "bin" / config / FRAMEWORK

    shutil.rmtree(BIN_PATH, ignore_errors=True)
    shutil.copytree(out_path, BIN_PATH, dirs_exist_ok=True)

    copy_package_dlls()


if __name__ == "__main__":
    main()
