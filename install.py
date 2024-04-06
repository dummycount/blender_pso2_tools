from pathlib import Path
import sys
import subprocess

REPO_PATH = Path(__file__).parent
BUILD_SCRIPT = REPO_PATH / "scripts" / "build.py"
INSTALL_SCRIPT = REPO_PATH / "scripts" / "install.py"


def main():
    subprocess.check_call(
        ["git", "submodule", "update", "--init", "--recursive"], cwd=REPO_PATH
    )
    subprocess.check_call([sys.executable, BUILD_SCRIPT])
    subprocess.check_call([sys.executable, INSTALL_SCRIPT])


if __name__ == "__main__":
    main()
