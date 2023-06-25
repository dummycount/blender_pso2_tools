#!/usr/bin/env python3

import os
from pathlib import Path


def version_to_tuple(path: Path):
    return tuple(int(x) for x in path.name.split("."))


def get_addon_path() -> Path:
    settings = Path(os.getenv("APPDATA")) / "Blender Foundation" / "Blender"

    versions = [path for path in settings.iterdir() if path.is_dir()]
    latest = max(versions, key=version_to_tuple)

    return latest / "scripts" / "addons" / "pso2_tools"


def main():
    target = get_addon_path()
    source = Path(__file__).parent / "pso2_tools"

    if target.exists():
        print(f"Already installed at \"{target}\"")
    else:
        print(f"Linking {target} to {source.relative_to(Path.cwd())}")

        source.parent.mkdir(exist_ok=True, parents=True)
        os.symlink(source, target, target_is_directory=True)


if __name__ == "__main__":
    main()
