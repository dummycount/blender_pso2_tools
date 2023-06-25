from pathlib import Path
import subprocess

BIN_DIR = Path(__file__).parent / "bin"
ICE_CLI = BIN_DIR / "ice.exe"
AQP2FBX = BIN_DIR / "aqp2fbx.exe"
FBX2AQP = BIN_DIR / "fbx2aqp.exe"
DDS2PNG = BIN_DIR / "dds2png.exe"


def run(args, **kwargs):
    return subprocess.run(
        args, check=True, capture_output=True, encoding="utf-8", **kwargs
    )


def aqp_to_fbx(model: Path, dest: Path, *args):
    return run([AQP2FBX, model, dest, *args])


def fbx_to_aqp(model: Path, dest: Path, *args):
    return run([FBX2AQP, model, dest, *args])


def dds_to_png(image: Path, dest: Path):
    return run([DDS2PNG, image, dest])


def unpack_ice(archive: Path, dest: Path, *args):
    return run([ICE_CLI, "unpack", archive, dest, *args])
