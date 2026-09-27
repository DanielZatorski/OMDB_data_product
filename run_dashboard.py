"""Launch the Streamlit dashboard.

    python run_dashboard.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
APP_PATH = ROOT_DIR / "dashboard" / "Welcome_Page.py"


def main():
    streamlit = shutil.which("streamlit")
    if not streamlit:
        sys.exit(
            "streamlit not found on PATH. See dbt_project/README.md's PATH note "
            "(same fix applies here)."
        )
    subprocess.run([streamlit, "run", str(APP_PATH)], cwd=ROOT_DIR)


if __name__ == "__main__":
    main()
