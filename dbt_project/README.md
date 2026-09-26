# dbt project — staging & gold layer

This is the "T" (transform) half of the pipeline. It takes the raw data the Python pipeline (`bronze_pipeline/`) already loaded into `data/warehouse.duckdb`, cleans it into **staging** (silver), and builds the **marts** (gold) — the star schema the dashboard reads from. See the root `README.md` for the *why* (data questions, KPIs, rules); this file is about the *how* of running and understanding this dbt project specifically.

## Before you run this

This dbt project doesn't create its own input data — it only reads from `raw.box_office` and `raw.omdb_responses`, which the Python pipeline builds. Run that first:
```
cd ..
python -m bronze_pipeline.selection   # only if you need to (re)decide which movies to fetch
python -m bronze_pipeline.run         # fetches OMDb + lands raw.* tables
cd dbt_project
```

## Running it

Always run these two things from inside `dbt_project/`, and always pass `--profiles-dir .` — the connection config (`profiles.yml`) lives in this folder, not the default `~/.dbt/` location dbt normally looks in.

```
dbt run --profiles-dir .     # builds every model (staging views + gold tables)
dbt test --profiles-dir .    # runs every test, tells you if anything's actually wrong
```

If `dbt: command not found` — either use the full path (`"C:\Users\<you>\AppData\Local\Programs\Python\Python313\Scripts\dbt.exe"`), or add that Scripts folder to PATH once (see project chat history / ask again if needed).

## Project structure

```
dbt_project/
  dbt_project.yml            project config: which folders are "staging" vs "marts", materialization type
  profiles.yml                 connection config: points at ../data/warehouse.duckdb
  macros/
    generate_schema_name.sql      makes schemas exactly "staging"/"marts" (dbt's default would be "main_staging")
  models/
    staging/
      _sources.yml                 declares raw.box_office / raw.omdb_responses as dbt's inputs
      _stg_models.yml               column-level tests for the staging models (see Tests below)
      stg_box_office.sql              cleans box office data: nulls the "-" distributor placeholder
      stg_omdb.sql                     cleans OMDb data: parses imdb_votes, derives omdb_matched/error_message
    marts/
      _marts_models.yml              column-level tests for the gold models (see Tests below)
      int_movie_performance.sql        intermediate: one row per movie, the box-office KPIs (not part of the ER diagram — a helper the marts below share)
      dim_movie.sql
      dim_distributor.sql
      dim_date.sql
      movie_genre.sql                   bridge table (genre is multi-valued)
      fact_movie_performance.sql
  tests/
    assert_no_negative_revenue.sql    hand-written checks that don't fit a generic test
    assert_no_negative_theaters.sql
    assert_omdb_match_rate.sql
    assert_no_duplicate_movie_identity.sql
    assert_legs_multiplier_valid.sql
    assert_dim_fact_row_count_match.sql
```

## Staging models (silver)

| Model | One row per | What it does |
|---|---|---|
| `stg_box_office` | movie × date | passes CSV rows through, only cleaning: `"-"` distributor → null |
| `stg_omdb` | movie | parses `imdb_votes` ("611,841" → `611841`), turns `Response`/`Error` into `omdb_matched`/`error_message`, nulls `"N/A"` values |

Query either one directly: `SELECT * FROM staging.stg_box_office LIMIT 10` (see the "exploring data" commands below).

One thing both staging models do: compute a normalized `title_key` (strip punctuation, lowercase) alongside the raw `title`. The same movie sometimes appears under two spellings in the source CSV (e.g. `"Jurassic World Dominion"` vs `"Jurassic World: Dominion"`) — without normalizing, that one movie would silently split into two fake movies downstream. `title_key` is how the gold layer joins staging back together correctly; it's never shown to the dashboard, just used for joining.

## Gold mart models

| Model | One row per | What it does |
|---|---|---|
| `int_movie_performance` | movie | intermediate (not in the ER diagram): aggregates `stg_box_office` into the box-office KPIs — release date, opening theaters, total gross, opening week gross, opening week per theater, legs multiplier |
| `dim_movie` | movie | movie identity, built straight from `stg_omdb` (already one row per movie) |
| `dim_distributor` | distributor | distinct distributor names, from each movie's opening-day distributor |
| `dim_date` | calendar date | the distinct release dates the fact table actually references |
| `movie_genre` | movie × genre | bridge table — explodes OMDb's comma-separated `Genre` into one row per genre |
| `fact_movie_performance` | movie | joins `int_movie_performance` + `stg_omdb`, resolves surrogate keys against the 3 dimensions |

`int_movie_performance` is a deliberate extra step: `dim_distributor`, `dim_date`, and `fact_movie_performance` all need the same per-movie aggregation (release date, opening-day distributor, etc.), so it's computed once here rather than three times.

## Tests

`dbt test` runs 37 tests total — 6 hand-written singular tests (in `tests/`), 31 auto-generated from the `tests:` blocks in `_stg_models.yml` and `_marts_models.yml` (no SQL to write for those, dbt does it from the YAML).

A test result is one of:
- **PASS** — no problem found.
- **WARN** — found rows that violate the check, but it's a *known, tolerated* issue (configured with `severity: warn`), not a build-breaking bug.
- **ERROR** — something's actually wrong; would fail a CI pipeline.

Current results: **34 PASS, 3 WARN, 0 ERROR**. The 3 warnings are all the same known, tolerated source-data gaps: 16 rows with a genuinely missing `theaters` value (staging), 363 rows where `distributor` was the `"-"` placeholder (now nulled, staging), and 4 movies whose opening-day row happens to be one of those 16 (so `opening_theaters` is null for those 4 in the gold fact table too). None of these are bugs — they're documented data-quality findings from the source CSV, deliberately set to `warn` rather than `error`.

Three tests are worth calling out specifically, since they're not generic boilerplate — they encode real invariants discovered while building this:
- `assert_no_duplicate_movie_identity` — no two `dim_movie` rows share a (title, release_year). This is the test that would have directly caught the "Jurassic World Dominion" vs "Jurassic World: Dominion" bug had it existed sooner.
- `assert_legs_multiplier_valid` — `total_gross` can never be less than `opening_week_gross` (the opening week is a subset of the total run); a violation means the aggregation logic itself is broken.
- `assert_dim_fact_row_count_match` — `dim_movie` and `fact_movie_performance` must have exactly the same row count, since the fact's grain is "one row per movie."

## Exploring the data

| Command | What it's for |
|---|---|
| `dbt show --select stg_box_office --limit 10` | preview a model's output |
| `dbt show --inline "select * from {{ ref('stg_box_office') }} where revenue > 1000000" --limit 20` | ad-hoc query using `ref()` — **don't** put `limit` inside the SQL string, use the `--limit` flag instead, or you'll get a double-LIMIT syntax error |
| `dbt list --profiles-dir .` | list every model/source/test in the project |
| `dbt compile --select stg_omdb` | see the literal SQL a model compiles to (under `target/compiled/...`) |
| `dbt docs generate && dbt docs serve` | interactive docs site with the full lineage graph — genuinely useful now that there are 8 models to see connected |

For anything beyond a quick preview (filtering, aggregating, joining), plain Python is often faster:
```python
import duckdb
con = duckdb.connect("../data/warehouse.duckdb")
print(con.execute("SELECT * FROM staging.stg_box_office WHERE revenue > 1000000 LIMIT 20").fetchdf())
```
