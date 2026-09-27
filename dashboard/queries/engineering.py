"""Data engineering metrics — record counts, freshness, quality, execution info.

Everything here reads from something that genuinely already exists (live
DuckDB tables, dbt's own run_results.json, or the bronze_pipeline run log) —
nothing on this page is fabricated. Where a real signal doesn't exist, the
function returns None and the page says so rather than showing a fake number.
"""

import json
from datetime import datetime, timezone

import pandas as pd

from db import DBT_TARGET_DIR, DUCKDB_PATH, LAST_RUN_LOG, run_query

TABLES = [
    ("Bronze (raw schema)", "raw", "box_office"),
    ("Bronze (raw schema)", "raw", "omdb_responses"),
    ("Silver (staging)", "staging", "stg_box_office"),
    ("Silver (staging)", "staging", "stg_omdb"),
    ("Gold (marts)", "marts", "dim_movie"),
    ("Gold (marts)", "marts", "dim_distributor"),
    ("Gold (marts)", "marts", "dim_date"),
    ("Gold (marts)", "marts", "movie_genre"),
    ("Gold (marts)", "marts", "fact_movie_performance"),
]


def record_counts() -> pd.DataFrame:
    rows = []
    for layer, schema, table in TABLES:
        count = int(run_query(f"select count(*) as c from {schema}.{table}")["c"][0])
        rows.append({"layer": layer, "table": f"{schema}.{table}", "row_count": count})
    return pd.DataFrame(rows)


def read_dbt_run_results() -> dict | None:
    path = DBT_TARGET_DIR / "run_results.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def dbt_execution_summary() -> dict | None:
    """Whatever the *last* dbt invocation was (run, test, or build) — dbt
    overwrites run_results.json each time, so this reflects only that last
    command, not necessarily both models and tests."""
    data = read_dbt_run_results()
    if not data:
        return None

    rows = []
    for r in data["results"]:
        parts = r["unique_id"].split(".")
        rows.append(
            {
                "kind": parts[0],
                "name": parts[-1],
                "status": r["status"],
                "execution_time_s": round(r["execution_time"], 3),
                "failures": r.get("failures") or 0,
            }
        )
    return {
        "generated_at": data["metadata"]["generated_at"],
        "results": pd.DataFrame(rows),
    }


def read_last_pipeline_run() -> dict | None:
    """The bronze_pipeline run log (bronze_pipeline/run.py writes this after
    every run). None if the pipeline has never been run since this dashboard
    was added."""
    if not LAST_RUN_LOG.exists():
        return None
    return json.loads(LAST_RUN_LOG.read_text(encoding="utf-8"))


def flagged_records() -> pd.DataFrame:
    """Rows that failed a data-quality check but were kept, not dropped.

    This pipeline deliberately never discards rows that fail a check — it
    flags them (README section 4) and carries them through, since silently
    dropping data hides the problem rather than reporting it. These are the
    known, tolerated cases, not bugs — see dbt_project/README.md's Tests
    section for why each one is a warn, not an error.
    """
    checks = [
        ("stg_box_office.theaters missing", "select count(*) as c from staging.stg_box_office where theaters is null"),
        ("stg_box_office.distributor missing", "select count(*) as c from staging.stg_box_office where distributor is null"),
        (
            "fact_movie_performance.opening_theaters missing",
            "select count(*) as c from marts.fact_movie_performance where opening_theaters is null",
        ),
        ("stg_omdb unmatched to OMDb", "select count(*) as c from staging.stg_omdb where not omdb_matched"),
    ]
    rows = [{"check": label, "flagged_rows": int(run_query(sql)["c"][0])} for label, sql in checks]
    return pd.DataFrame(rows)


def freshness() -> dict:
    """The real freshness signals available: the warehouse file's last
    modification time, and (if it exists) dbt's own last-invocation timestamp.
    There's no separate freshness/timestamp column tracked anywhere else."""
    info = {}
    if DUCKDB_PATH.exists():
        mtime = datetime.fromtimestamp(DUCKDB_PATH.stat().st_mtime, tz=timezone.utc)
        info["warehouse_file_last_modified"] = mtime

    dbt_data = read_dbt_run_results()
    if dbt_data:
        info["dbt_last_invocation"] = dbt_data["metadata"]["generated_at"]

    return info
