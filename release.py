from itertools import chain
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO_PATH = Path(__file__).parent
ADDON_PATH = REPO_PATH / "pso2_tools"


def get_version():
    init = ADDON_PATH / "__init__.py"
    with init.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith('"version"'):
                version = line.partition(":")[2]
                parts = version.strip().removeprefix("(").removesuffix("),").split(",")

                return ".".join(part.strip() for part in parts)

    return "0.0.0"


def main():
    path = Path(f"pso2_tools-v{get_version()}.zip")

    with ZipFile(path, "w", compression=ZIP_DEFLATED) as zip:
        files = ADDON_PATH.rglob("*")

        # https://github.com/python/cpython/issues/77609
        bin_files = (ADDON_PATH / "bin").rglob("*")

        for path in set(chain(files, bin_files)):
            if path.suffix == ".pyc" or path.name == "__pycache__":
                continue

            zip.write(path, path.relative_to(REPO_PATH))


if __name__ == "__main__":
    main()
