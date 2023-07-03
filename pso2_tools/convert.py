from pathlib import Path
import subprocess

BIN_DIR = Path(__file__).parent / "bin"
PSO_CLI = BIN_DIR / "pso.exe"
ICE_CLI = BIN_DIR / "ice.exe"


def run(args, **kwargs):
    return subprocess.run(
        args, check=True, capture_output=True, encoding="utf-8", **kwargs
    )


def aqp_to_fbx(model: Path, dest: Path, *args):
    return run([PSO_CLI, "fbx", model, dest, *args])


def fbx_to_aqp(model: Path, dest: Path, *args):
    return run([PSO_CLI, "aqp", model, dest, *args])


def unpack_ice(archive: Path, dest: Path, *args):
    return run([ICE_CLI, "unpack", archive, dest, *args])


def make_file_lists(pso2_bin: Path, dest: Path, *args):
    return run([PSO_CLI, "filelist", dest, "--bin", pso2_bin, *args])
