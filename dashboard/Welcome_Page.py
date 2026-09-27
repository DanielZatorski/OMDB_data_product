import streamlit as st

from db import run_query
from queries.base import MOVIE_FACTS_CTE

st.set_page_config(page_title="OMDB Data Product", layout="wide")

st.title("Movies Dashboard")
st.caption(
    "Box office revenue (2013-2022, 950 movies) enriched with OMDb ratings"
)

summary = run_query(
    MOVIE_FACTS_CTE
    + """
    select
        count(*) as movie_count,
        sum(total_gross) as total_gross,
        min(release_year) as first_year,
        max(release_year) as last_year,
        sum(case when omdb_matched then 1 else 0 end) * 100.0 / count(*) as match_rate_pct
    from movie_facts
    """
)
row = summary.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Movies", f"{int(row['movie_count']):,}")
col2.metric("Combined gross", f"${row['total_gross'] / 1e9:.2f}B")
col3.metric("Years covered", f"{int(row['first_year'])}-{int(row['last_year'])}")
col4.metric("OMDb match rate", f"{row['match_rate_pct']:.1f}%")

st.divider()

st.markdown(
    """
### Pages

- **Business Analytics** — the ranking dashboard: top movies, distributors,
  genres, ratings vs. revenue
- **Data Quality** — record counts, freshness, data quality test
  results, flagged records, and pipeline execution info from dbt project
"""
)
