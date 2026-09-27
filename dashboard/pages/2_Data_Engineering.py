import streamlit as st

from queries import engineering

st.set_page_config(page_title="Data Engineering", layout="wide")
st.title("Data Quality")
st.caption("Every number on this page reads from something that actually exists — live table counts, dbt's own run artifacts, or the pipeline's run log. Nothing here is simulated.")

st.header("Processed record counts")
st.caption("Live row counts per table, across all 3 layers.")
st.dataframe(engineering.record_counts(), width="stretch", hide_index=True)

st.divider()

st.header("Freshness")
fresh = engineering.freshness()
col1, col2 = st.columns(2)
if "warehouse_file_last_modified" in fresh:
    col1.metric("Warehouse file last modified", fresh["warehouse_file_last_modified"].strftime("%Y-%m-%d %H:%M UTC"))
else:
    col1.info("data/warehouse.duckdb not found.")
if "dbt_last_invocation" in fresh:
    col2.metric("dbt last invocation", fresh["dbt_last_invocation"][:19].replace("T", " ") + " UTC")
else:
    col2.info("No dbt run_results.json yet — run `dbt run` or `dbt test`.")

st.divider()

st.header("Data quality metrics")
dbt_summary = engineering.dbt_execution_summary()
if dbt_summary is None:
    st.info("No dbt run_results.json found. Run `python run_pipeline.py dbt-test` first.")
else:
    results = dbt_summary["results"]
    tests = results[results["kind"] == "test"]
    models = results[results["kind"] == "model"]

    if not tests.empty:
        pass_count = int((tests["status"] == "pass").sum())
        warn_count = int((tests["status"] == "warn").sum())
        error_count = int((tests["status"] == "error").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Tests passed", pass_count)
        c2.metric("Tests warned", warn_count, help="Known, tolerated data-quality gaps — see README section 4.")
        c3.metric("Tests errored", error_count)
        st.dataframe(
            tests[["name", "status", "failures", "execution_time_s"]].sort_values("status"),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "The last dbt invocation didn't include tests (it ran models only). "
            "Run `python run_pipeline.py dbt-test` to refresh this."
        )

    if not models.empty:
        st.subheader("Model build results (from the same last invocation)")
        st.dataframe(models[["name", "status", "execution_time_s"]], width="stretch", hide_index=True)

st.divider()

st.header("Flagged records")
st.caption(
    "This pipeline never silently drops a row that fails a check — it flags it and keeps it "
    "(README section 4). These are the counts of flagged rows per check, not rejections."
)
st.dataframe(engineering.flagged_records(), width="stretch", hide_index=True)

st.divider()

st.header("Pipeline execution information")
last_run = engineering.read_last_pipeline_run()
if last_run is None:
    st.info(
        "No bronze_pipeline run log found yet (data/bronze/last_run.json). "
        "Run `python run_pipeline.py fetch` (or `all`) to generate one."
    )
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last run at", last_run["run_at"][:19].replace("T", " "))
    c2.metric("Movies requested", last_run["movies_requested"])
    c3.metric("OMDb matched", f"{last_run['omdb_matched']} ({last_run['omdb_match_rate_pct']:.1f}%)")
    c4.metric("Box office rows loaded", f"{last_run['box_office_rows_loaded']:,}")

if dbt_summary is not None:
    st.caption(f"dbt artifacts generated at: {dbt_summary['generated_at']}")
