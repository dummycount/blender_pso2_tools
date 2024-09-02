import tomllib
from pathlib import Path

from blender import blender_call

ROOT = Path(__file__).parent.parent
SOURCE_DIR = ROOT / "pso2_tools"
OUTPUT_DIR = ROOT / "dist"

MANIFEST = SOURCE_DIR / "blender_manifest.toml"

def build():
    blender_call(
        [
            "-c",
            "extension",
            "build",
            "--source-dir",
            SOURCE_DIR,
            "--output-dir",
            OUTPUT_DIR,
        ]
    )

    return get_package_path()

def get_package_path() -> Path:
    with MANIFEST.open('rb') as f:
        manifest = tomllib.load(f)
        name = f"{manifest["id"]}-{manifest['version']}.zip"

        return OUTPUT_DIR / name


if __name__ == "__main__":
    build()
