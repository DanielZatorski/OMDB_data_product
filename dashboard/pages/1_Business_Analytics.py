import altair as alt
import streamlit as st

from queries import distributors, genres, monthly, rankings

st.set_page_config(page_title="Business Analytics", layout="wide")
st.title("Business Analytics")

years = rankings.available_years()
with st.sidebar:
    st.header("Filters")
    year_choice = st.selectbox("Year", options=["All years"] + years, index=0)
    year = None if year_choice == "All years" else int(year_choice)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Top movies (Q1)",
        "Distributors (Q2, Q5)",
        "Word of mouth (Q3)",
        "Release month (Q4)",
        "Genres (Q6, Q7)",
        "Ratings (Q8, Q9)",
    ]
)

with tab1:
    st.subheader("Top 10 movies by total gross")
    df = rankings.top_movies_by_gross(year, limit=10)
    chart = (
        alt.Chart(df)
        .mark_bar(color="#4C78A8", cornerRadiusEnd=4)
        .encode(
            x=alt.X("total_gross:Q", title="Total gross ($)"),
            y=alt.Y("title:N", sort="-x", title=None),
            tooltip=["title", "release_year", "total_gross"],
        )
    )
    st.altair_chart(chart, width="stretch")
    st.dataframe(df, width="stretch", hide_index=True)

with tab2:
    st.subheader("Strongest openings by distributor (opening gross per theater)")
    st.caption("R1 wide releases only, R3 sum ÷ sum (not the average of ratios).")
    df_open = distributors.strongest_openings(year, limit=10)
    chart = (
        alt.Chart(df_open)
        .mark_bar(color="#4C78A8", cornerRadiusEnd=4)
        .encode(
            x=alt.X("opening_week_per_theater:Q", title="Opening week gross / theater ($)"),
            y=alt.Y("distributor_name:N", sort="-x", title=None),
            tooltip=["distributor_name", "opening_week_per_theater", "movie_count"],
        )
    )
    st.altair_chart(chart, width="stretch")
    st.dataframe(df_open, width="stretch", hide_index=True)

    st.subheader("Distributor market share by year")
    y_from, y_to = years[0], years[-1]
    df_share = distributors.market_share_by_year(y_from, y_to)
    share_chart = (
        alt.Chart(df_share)
        .mark_area()
        .encode(
            x=alt.X("release_year:O", title="Year"),
            y=alt.Y("market_share:Q", stack="normalize", axis=alt.Axis(format="%"), title="Market share"),
            color=alt.Color("distributor_name:N", legend=None),
            tooltip=["release_year", "distributor_name", alt.Tooltip("market_share:Q", format=".1%")],
        )
    )
    st.altair_chart(share_chart, width="stretch")
    st.caption("Computed live from the active year range — not stored (README section 2).")

with tab3:
    st.subheader("Best word of mouth (highest legs multiplier)")
    st.caption("Legs multiplier = total gross ÷ opening week gross.")
    wide_only_q3 = st.checkbox(
        "Wide releases only (≥ 600 theaters)",
        value=True,
        help="R1: small releases distort per-theater and legs comparisons.",
        key="wide_only_q3",
    )
    df = rankings.best_word_of_mouth(year, wide_only_q3, limit=10)
    chart = (
        alt.Chart(df)
        .mark_bar(color="#4C78A8", cornerRadiusEnd=4)
        .encode(
            x=alt.X("legs_multiplier:Q", title="Legs multiplier"),
            y=alt.Y("title:N", sort="-x", title=None),
            tooltip=["title", "release_year", "legs_multiplier", "total_gross"],
        )
    )
    st.altair_chart(chart, width="stretch")
    st.dataframe(df, width="stretch", hide_index=True)

with tab4:
    st.subheader("Which release month gives the biggest openings")
    wide_only_q4 = st.checkbox(
        "Wide releases only (≥ 600 theaters)",
        value=True,
        help="R1: small releases distort per-theater and legs comparisons.",
        key="wide_only_q4",
    )
    df = monthly.openings_by_month(wide_only=wide_only_q4)
    chart = (
        alt.Chart(df)
        .mark_bar(color="#4C78A8", cornerRadiusEnd=4)
        .encode(
            x=alt.X("release_month_name:N", sort=list(df["release_month_name"]), title=None),
            y=alt.Y("avg_opening_week_gross:Q", title="Avg opening week gross ($)"),
            tooltip=["release_month_name", "avg_opening_week_gross", "movie_count"],
        )
    )
    st.altair_chart(chart, width="stretch")
    st.dataframe(df, width="stretch", hide_index=True)

with tab5:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top-grossing movie per genre")
        st.dataframe(genres.top_movie_per_genre(year), width="stretch", hide_index=True)
    with col_b:
        st.subheader("Genres that earn the most")
        st.caption("R4: a movie counts in every genre it has, so totals overlap.")
        df_genre = genres.genre_totals(year)
        chart = (
            alt.Chart(df_genre)
            .mark_bar(color="#4C78A8", cornerRadiusEnd=4)
            .encode(
                x=alt.X("total_gross:Q", title="Total gross ($)"),
                y=alt.Y("genre:N", sort="-x", title=None),
                tooltip=["genre", "total_gross", "movie_count"],
            )
        )
        st.altair_chart(chart, width="stretch")

with tab6:
    st.subheader("Best-rated movie" + (f" of {year}" if year else " each year"))
    min_votes = st.number_input(
        "Minimum IMDb votes",
        min_value=0,
        value=10_000,
        step=1_000,
        help="R2: stops a film rated by a few people from winning.",
    )
    st.dataframe(rankings.best_rated(year, min_votes, limit=10), width="stretch", hide_index=True)

    st.subheader("Do higher-rated movies earn more?")
    df_corr = rankings.rating_vs_revenue(min_votes)
    corr = df_corr["imdb_rating"].corr(df_corr["total_gross"])
    st.metric("Correlation (rating vs. total gross)", f"{corr:.2f}")
    scatter = (
        alt.Chart(df_corr)
        .mark_circle(color="#4C78A8", opacity=0.6, size=60)
        .encode(
            x=alt.X("imdb_rating:Q", title="IMDb rating"),
            y=alt.Y("total_gross:Q", title="Total gross ($)", scale=alt.Scale(type="log")),
            tooltip=["title", "release_year", "imdb_rating", "total_gross"],
        )
    )
    st.altair_chart(scatter, width="stretch")
