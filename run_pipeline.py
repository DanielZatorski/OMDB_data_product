"""End-to-end pipeline orchestrator.

Run one step at a time:
    python run_pipeline.py select      # decide which movies to fetch (manual, deliberate — see README)
    python run_pipeline.py fetch       # call OMDb, land raw tables in DuckDB
    python run_pipeline.py dbt-run     # build staging + gold models
    python run_pipeline.py dbt-test    # run all dbt tests

Or everything except `select` (fetch -> dbt-run -> dbt-test), in order:
    python run_pipeline.py all
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DBT_PROJECT_DIR = ROOT_DIR / "dbt_project"

# `select` is deliberately excluded from `all` — it decides which movies get
# fetched, and that should only ever happen when you explicitly ask for it,
# not silently on every full-pipeline run.
ALL_STEPS = ["fetch", "dbt-run", "dbt-test"]


def run(cmd, cwd):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def require_dbt():
    dbt = shutil.which("dbt")
    if not dbt:
        sys.exit("dbt not found on PATH. See dbt_project/README.md for the PATH fix.")
    return dbt


def step_select():
    run([sys.executable, "-m", "bronze_pipeline.selection"], cwd=ROOT_DIR)


def step_fetch():
    run([sys.executable, "-m", "bronze_pipeline.run"], cwd=ROOT_DIR)


def step_dbt_run():
    run([require_dbt(), "run", "--profiles-dir", "."], cwd=DBT_PROJECT_DIR)


def step_dbt_test():
    run([require_dbt(), "test", "--profiles-dir", "."], cwd=DBT_PROJECT_DIR)


STEP_FUNCS = {
    "select": step_select,
    "fetch": step_fetch,
    "dbt-run": step_dbt_run,
    "dbt-test": step_dbt_test,
}


def main():
    parser = argparse.ArgumentParser(description="Run the OMDB data product pipeline.")
    parser.add_argument(
        "step",
        choices=[*STEP_FUNCS.keys(), "all"],
        help="Which step to run, or 'all' for fetch -> dbt-run -> dbt-test in order.",
    )
    args = parser.parse_args()

    steps = ALL_STEPS if args.step == "all" else [args.step]
    for step in steps:
        STEP_FUNCS[step]()

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
