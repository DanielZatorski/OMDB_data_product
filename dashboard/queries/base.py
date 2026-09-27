"""Shared CTE joining fact_movie_performance to all 3 dimensions.

Every business-analytics query builds on this one join, so the grain and the
column names stay consistent across Q1-Q9 instead of being re-derived per query.
"""

MOVIE_FACTS_CTE = """
with movie_facts as (
    select
        dm.movie_key,
        dm.title,
        dm.release_year,
        dm.imdb_id,
        dm.omdb_matched,
        dd.distributor_name,
        ddt.date as release_date,
        ddt.month as release_month,
        ddt.month_name as release_month_name,
        f.opening_theaters,
        f.is_wide_release,
        f.total_gross,
        f.opening_week_gross,
        f.opening_week_per_theater,
        f.legs_multiplier,
        f.imdb_rating,
        f.imdb_votes
    from marts.fact_movie_performance f
    join marts.dim_movie dm on f.movie_key = dm.movie_key
    left join marts.dim_distributor dd on f.distributor_key = dd.distributor_key
    left join marts.dim_date ddt on f.release_date_key = ddt.date_key
)
"""
