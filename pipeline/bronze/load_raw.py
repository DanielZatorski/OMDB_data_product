import duckdb
import pandas as pd

from pipeline.config import DUCKDB_PATH
from pipeline.bronze.selection import title_key


def load_raw(box_office_df: pd.DataFrame, selected_movies: pd.DataFrame, omdb_df: pd.DataFrame) -> None:
    """Land the selected movies' data into DuckDB's raw schema, unmodified
    (README section 5, pipeline step 5). Cleaning happens later, in dbt's
    staging models — this step only filters to the selected movies and
    writes what was extracted, as-is.

    Joins on the same normalized title_key selection.py groups by, so every
    spelling variant of a selected movie's title (e.g. "Jurassic World
    Dominion" vs "Jurassic World: Dominion") is included, not just whichever
    spelling ended up as the display title.
    """
    box_office = box_office_df.copy()
    box_office["title_key"] = box_office["title"].map(title_key)
    box_office["release_year"] = box_office.groupby("title_key")["date"].transform("min").dt.year

    selected = selected_movies.copy()
    selected["title_key"] = selected["title"].map(title_key)

    key_cols = ["title_key", "release_year"]
    filtered_box_office = box_office.merge(selected[key_cols], on=key_cols, how="inner").drop(columns=["title_key"])

    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("CREATE OR REPLACE TABLE raw.box_office AS SELECT * FROM filtered_box_office")
        con.execute("CREATE OR REPLACE TABLE raw.omdb_responses AS SELECT * FROM omdb_df")
    finally:
        con.close()

    print(f"Loaded {len(filtered_box_office)} box office rows and {len(omdb_df)} OMDb rows into raw schema")
