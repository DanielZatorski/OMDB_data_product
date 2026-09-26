import json
import re
import time

import pandas as pd
import requests

from pipeline.config import OMDB_API_KEY, OMDB_BASE_URL, OMDB_BRONZE_DIR

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1
REQUEST_DELAY_SECONDS = 0.1


def _cache_path(title: str, year: int):
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return OMDB_BRONZE_DIR / f"{slug}_{year}.json"


def _request_omdb(title: str, year: int) -> dict:
    params = {"apikey": OMDB_API_KEY, "t": title, "y": year, "type": "movie"}
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
    return {"Response": "False", "Error": f"request failed: {last_error}"}


def fetch_all(selected_movies: pd.DataFrame) -> pd.DataFrame:
    """Call OMDb for each selected movie, caching raw responses in bronze
    (README section 5, pipeline step 4). A movie already cached is never
    re-requested, so reruns never spend extra quota.
    """
    OMDB_BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    matched = 0
    for _, row in selected_movies.iterrows():
        title, year = row["title"], int(row["release_year"])
        path = _cache_path(title, year)

        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
        else:
            raw = _request_omdb(title, year)
            path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
            time.sleep(REQUEST_DELAY_SECONDS)

        if raw.get("Response") == "True":
            matched += 1

        records.append(
            {
                "requested_title": title,
                "requested_year": year,
                "imdb_id": raw.get("imdbID"),
                "title": raw.get("Title"),
                "year": raw.get("Year"),
                "genre": raw.get("Genre"),
                "imdb_rating": raw.get("imdbRating"),
                "imdb_votes": raw.get("imdbVotes"),
                "response": raw.get("Response"),
                "error": raw.get("Error"),
            }
        )

    print(f"OMDb match rate: {matched}/{len(selected_movies)}")
    return pd.DataFrame.from_records(records)
