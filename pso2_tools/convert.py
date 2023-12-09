from pathlib import Path
import subprocess

from .aqp_info import AqpInfo

BIN_DIR = Path(__file__).parent / "bin"
PSO_CLI = BIN_DIR / "pso.exe"


def run(args, **kwargs):
    return subprocess.run(
        args, check=True, capture_output=True, encoding="utf-8", **kwargs
    )


def aqp_to_fbx(model: Path, dest: Path, *args):
    return run([PSO_CLI, "convert", "fbx", model, dest, *args])


def aqp_to_fbx_with_info(model: Path, dest: Path) -> AqpInfo:
    result = aqp_to_fbx(model, dest, "--info")

    # https://github.com/lidatong/dataclasses-json/issues/198
    # pylint: disable=no-member
    return AqpInfo.from_json(result.stdout)


def fbx_to_aqp(model: Path, dest: Path, *args):
    return run([PSO_CLI, "convert", "aqp", model, dest, *args])


def make_file_lists(pso2_bin: Path, dest: Path, *args):
    return run([PSO_CLI, "cmx", "sheets", dest, "--bin", pso2_bin, *args])


def make_color_channels(pso2_bin: Path, dest: Path, *args):
    result = run([PSO_CLI, "cmx", "colorchannels", "--bin", pso2_bin, *args])

    dest.parent.mkdir(exist_ok=True, parents=True)
    with dest.open("w") as f:
        f.write(result.stdout)
