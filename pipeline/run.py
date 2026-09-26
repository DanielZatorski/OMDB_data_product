import pandas as pd

from pipeline.config import MOVIES_INPUT_CSV
from pipeline.bronze.extract import extract
from pipeline.bronze.fetch_omdb import fetch_all
from pipeline.bronze.load_raw import load_raw


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

    print("Done.")


if __name__ == "__main__":
    main()
