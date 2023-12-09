import os
from pathlib import Path
import subprocess

REPO_PATH = Path(__file__).parent
ADDON_PATH = REPO_PATH / "pso2_tools"
CLI_PATH = REPO_PATH / "Pso2Cli"


def main():
    if not CLI_PATH.exists():
        subprocess.check_call(["git", "submodule", "update", "--init", "--recursive"])

    subprocess.check_call(["pwsh", CLI_PATH / "BuildRelease.ps1"], cwd=CLI_PATH)

    bin_source = CLI_PATH / "Release" / "Pso2Cli"
    bin_target = ADDON_PATH / "bin"

    if not bin_target.exists():
        os.symlink(bin_source, bin_target, target_is_directory=True)


if __name__ == "__main__":
    main()
