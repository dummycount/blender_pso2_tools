import argparse
import shutil

import build_package
from blender import blender_call, get_extension_repo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--editable",
        action="store_true",
        help="Install in editable mode (symlink extension folder to this repo)",
    )
    parser.add_argument("--repo", "-r", default="user_default")

    args = parser.parse_args()

    package = build_package.build()
    blender_call(
        ["-c", "extension", "install-file", "-r", args.repo, "--enable", package]
    )

    if args.editable:
        repo_path = get_extension_repo(args.repo)
        if repo_path is None:
            print(f'Cannot make editable. Couldn\'t find repo "{args.repo}"')
            return

        source_path = build_package.SOURCE_DIR
        dest_path = repo_path / source_path.name

        shutil.rmtree(dest_path, ignore_errors=True)
        dest_path.symlink_to(source_path, target_is_directory=True)


if __name__ == "__main__":
    main()
