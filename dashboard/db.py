"""Shared DuckDB connection + query caching for the dashboard.

Read-only on purpose: the dashboard only ever reads from data/warehouse.duckdb,
it never writes to it — that's the pipeline's job (bronze_pipeline/ + dbt).
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
DUCKDB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"
DBT_TARGET_DIR = ROOT_DIR / "dbt_project" / "target"
LAST_RUN_LOG = ROOT_DIR / "data" / "bronze" / "last_run.json"


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


@st.cache_data(ttl=300)
def run_query(sql: str, params: list | None = None) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql, params or []).fetchdf()
