# bronze_pipeline (Python — extract, select, fetch, load raw)

This is the "EL" (extract + load) half of the pipeline. It reads the box office CSV, decides which movies to enrich, calls the OMDb API, and lands everything unmodified into `data/warehouse.duckdb`'s `raw` schema. See the root `README.md` for the *why* (data questions, KPIs, movie-selection rule); this file is about the *how* of this specific package.

Nothing in this package cleans, joins, or aggregates data — that's deliberately dbt's job (`dbt_project/README.md`), not this one's.

## Before you run this

You need an OMDb API key. Register at omdbapi.com, then add it to `.env` at the repo root:
```
OMDB_API_KEY=your_key_here
```
You also need `data/bronze/box_office/revenues_per_day.csv` to already exist (the raw source CSV).

## Running it

```
python -m bronze_pipeline.selection   # decides which movies to fetch (see "Why selection is manual" below)
python -m bronze_pipeline.run          # calls OMDb, lands raw.* tables in DuckDB
```
Run both from the **repo root**, not from inside `bronze_pipeline/` — the `-m` flag needs the package importable from the root. `run_pipeline.py` at the repo root wraps these as `select`/`fetch` if you'd rather not remember the exact commands.

## Directory structure

```
bronze_pipeline/
  __init__.py
  config.py               paths + settings: API key (from .env), file locations, MOVIES_PER_YEAR/YEARS_SELECTED
  extract.py                read the full box office CSV into a DataFrame
  selection.py                standalone: aggregate + pick which movies to fetch, writes selected_movies.csv
  fetch_omdb.py                 call OMDb per movie, with bronze caching (see below)
  load_raw.py                     land box_office + OMDb data into DuckDB's raw schema
  run.py                          orchestrator for fetch_omdb.py + load_raw.py; writes data/bronze/last_run.json
  selected_movies.csv               the pipeline's input — see "Why this file lives here" below
```

## Why `selected_movies.csv` lives here, not in `data/bronze/`

It went through a couple of iterations before landing here. `data/bronze/` is for *raw data as delivered* (the README's own definition) — `selected_movies.csv` isn't that, it's the *output of a ranking decision* (`selection.py`'s top-95-per-year rule). It's not silver or gold either; it's closer to a pipeline input/config artifact — "here's the scope this run operates on." Keeping it next to the code that produces and consumes it (rather than mixed into the data folders) keeps that distinction clear.

## Why `selection.py` is a separate, manual step

`run.py` does **not** call `selection.py` automatically. This is deliberate: deciding which 950 movies to enrich is a business decision that should only change when you explicitly ask for it, not something the pipeline silently redoes (and potentially re-selects a different set of movies) on every run. `run.py` just reads whatever's currently in `selected_movies.csv` — it doesn't know or care how that list was produced. You could hand-edit that CSV yourself and `run.py` would work identically.

## The quota-safe cache

OMDb's free tier allows 1,000 requests/day. `fetch_omdb.py` protects that budget: before calling the API for any movie, it checks whether `data/bronze/omdb/<slug>.json` already exists — if so, it reads the cached file instead of calling OMDb again. This means reruns are always safe and (mostly) free: only movies newly added to `selected_movies.csv` since the last run actually spend quota.

One consequence worth knowing: because caching is permanent, a movie's OMDb data (rating, vote count) is frozen at whatever it was the day it was first fetched — reruns never refresh it. To force a re-pull for one movie, delete its file from `data/bronze/omdb/` before rerunning.

## Title normalization

The same movie can appear under slightly different spellings in the source CSV (e.g. `"Jurassic World Dominion"` vs `"Jurassic World: Dominion"`) — a real bug found while building this project, where one movie's revenue silently split across two fake "movies." `selection.py` defines a `title_key()` helper (strip punctuation, lowercase) used for *grouping* movies, while the original, cleanly-spelled title is kept for display and for the OMDb lookup. `load_raw.py` imports this same function so the box-office rows loaded into `raw.box_office` are filtered using the identical normalization — otherwise the two problems would resurface independently at each layer.

## What this package produces

- `data/bronze/omdb/*.json` — one raw OMDb response per selected movie (950 files)
- `raw.box_office`, `raw.omdb_responses` in `data/warehouse.duckdb` — unmodified, ready for dbt's `sources.yml` to build from
- `data/bronze/last_run.json` — a small run log (timestamp, movies requested, match rate, rows loaded), read by the dashboard's Data Engineering page
