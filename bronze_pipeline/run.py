import json
from datetime import datetime, timezone

import duckdb
import pandas as pd

from bronze_pipeline.config import DUCKDB_PATH, MOVIES_INPUT_CSV, ROOT_DIR
from bronze_pipeline.extract import extract
from bronze_pipeline.fetch_omdb import fetch_all
from bronze_pipeline.load_raw import load_raw

LAST_RUN_LOG = ROOT_DIR / "data" / "bronze" / "last_run.json"


def main():
    if not MOVIES_INPUT_CSV.exists():
        raise FileNotFoundError(
            f"{MOVIES_INPUT_CSV} not found. Run select.py first (or provide your own "
            f"CSV with title/release_year columns at that path) to decide which movies "
            f"this pipeline should fetch."
        )

    print(f"Reading movies to fetch from {MOVIES_INPUT_CSV}...")
    selected_movies = pd.read_csv(MOVIES_INPUT_CSV)
    print(f"{len(selected_movies)} movies")

    print("Extracting box office CSV...")
    df = extract()

    print("Fetching OMDb data...")
    omdb_df = fetch_all(selected_movies)

    print("Loading raw tables into DuckDB...")
    load_raw(df, selected_movies, omdb_df)

    matched = int(omdb_df["response"].eq("True").sum())
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    box_office_rows_loaded = con.execute("select count(*) from raw.box_office").fetchone()[0]
    con.close()

    run_log = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "movies_requested": len(selected_movies),
        "omdb_matched": matched,
        "omdb_match_rate_pct": round(100 * matched / len(selected_movies), 1),
        "box_office_rows_loaded": box_office_rows_loaded,
        "omdb_rows_loaded": len(omdb_df),
    }
    LAST_RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_LOG.write_text(json.dumps(run_log, indent=2), encoding="utf-8")

    print("Done.")


if __name__ == "__main__":
    main()
