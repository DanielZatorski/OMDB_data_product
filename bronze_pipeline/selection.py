"""Stand-alone step: decide which movies to fetch from OMDb.

Not called by run.py — this is a deliberate, separate decision that
produces the pipeline's input file. Run it directly to (re)generate that
file: `python select.py`.
"""

import re

import pandas as pd

from bronze_pipeline.config import MOVIES_INPUT_CSV, MOVIES_PER_YEAR, YEARS_SELECTED
from bronze_pipeline.extract import extract


def title_key(title: str) -> str:
    """Normalize a title for grouping only — not for display or OMDb lookup.

    The same movie sometimes appears under slightly different title
    strings in the CSV (e.g. "Jurassic World Dominion" vs "Jurassic World:
    Dominion"), which would otherwise split one movie's revenue across two
    fake "movies". Stripping punctuation merges those back together.
    """
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def select_movies(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate + select the top movies per year.

    Movie identity = title + release year (year of that title's first
    revenue date). Selects the top MOVIES_PER_YEAR movies by total gross
    for the YEARS_SELECTED most recent complete years in the CSV.
    """
    movie_agg = df.copy()
    movie_agg["title_key"] = movie_agg["title"].map(title_key)
    movie_agg["release_year"] = movie_agg.groupby("title_key")["date"].transform("min").dt.year

    # one display title per (title_key, release_year): whichever literal
    # spelling appears on the most rows
    display_titles = (
        movie_agg.groupby(["title_key", "release_year", "title"])
        .size()
        .reset_index(name="row_count")
        .sort_values("row_count", ascending=False)
        .drop_duplicates(["title_key", "release_year"])
        .rename(columns={"title": "display_title"})[["title_key", "release_year", "display_title"]]
    )

    movie_totals = (
        movie_agg.groupby(["title_key", "release_year"], as_index=False)["revenue"]
        .sum()
        .rename(columns={"revenue": "total_gross"})
        .merge(display_titles, on=["title_key", "release_year"])
        .drop(columns=["title_key"])
        .rename(columns={"display_title": "title"})
    )

    latest_year = movie_totals["release_year"].max()
    complete_years = sorted(y for y in movie_totals["release_year"].unique() if y < latest_year)
    selected_years = complete_years[-YEARS_SELECTED:]

    selected_movies = (
        movie_totals[movie_totals["release_year"].isin(selected_years)]
        .sort_values(["release_year", "total_gross"], ascending=[True, False])
        .groupby("release_year")
        .head(MOVIES_PER_YEAR)
        .reset_index(drop=True)
    )

    return selected_movies


if __name__ == "__main__":
    df = extract()
    selected = select_movies(df)
    selected[["title", "release_year", "total_gross"]].to_csv(MOVIES_INPUT_CSV, index=False)
    print(f"Wrote {len(selected)} movies to {MOVIES_INPUT_CSV}")
