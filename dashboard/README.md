# Dashboard (Streamlit)

Reads directly from `data/warehouse.duckdb` - read only. The dashboard is a pure consumer of the gold layer — writing/transforming data is `bronze_pipeline/`'s and dbt's job

## Running it

From the repo root:
```
python run_dashboard.py
```
That's a thin wrapper around `streamlit run dashboard/Welcome_Page.py`. You can also run that command directly.

## Directory structure

```
dashboard/
  Welcome_Page.py         entrypoint — the landing page
  pages/
    1_Business_Analytics.py   the ranking dashboard (Q1-Q9)
    2_Data_Engineering.py      record counts, freshness, quality, flagged records, execution info
  queries/
    base.py                  shared fact + dims join every business query builds on
    rankings.py                Q1, Q3, Q8, Q9
    distributors.py              Q2, Q5
    genres.py                     Q6, Q7
    monthly.py                     Q4
    engineering.py                   queries behind the Data Engineering page
  db.py                   the DuckDB connection + cached query runner everything else uses
```


## Caching

Two different `@st.cache_*` decorators are used in `db.py`, and they exist for different reasons:

```python
@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)

@st.cache_data(ttl=300)
def run_query(sql: str, params: list | None = None) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql, params or []).fetchdf()
```

- **`st.cache_resource`** is for objects that shouldn't be recreated or copied — like a database connection. Without it, Streamlit's "rerun the whole script on every click" model would open a brand new DuckDB connection on every single interaction. With it, `get_connection()` runs once per app process and every page/query reuses the same connection.
- **`st.cache_data`** is for return *values* — here, the DataFrame a query produces. It's keyed by the function's arguments (the SQL text + params), so asking for the same query twice returns the cached result instead of re-hitting DuckDB. `ttl=300` means each cached result expires after 5 minutes, so the dashboard doesn't need restarting to eventually pick up new data if the pipeline reruns in the background — worst case, a page is up to 5 minutes stale.

Both caches live **in memory, inside the running Streamlit process** — not on disk, not in DuckDB. Stopping and restarting `streamlit run` clears them; the next query just re-runs against DuckDB (still fast) and gets cached again from there. See the root project's chat history / ask again if you want the fuller explanation of why this matters for Streamlit's execution model.

