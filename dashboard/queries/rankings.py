"""Q1 (top movies), Q3 (word of mouth), Q8 (best-rated), Q9 (rating vs revenue)."""

import pandas as pd

from db import run_query
from queries.base import MOVIE_FACTS_CTE


def available_years() -> list[int]:
    sql = MOVIE_FACTS_CTE + "select distinct release_year from movie_facts order by release_year"
    return run_query(sql)["release_year"].tolist()


def top_movies_by_gross(year: int | None, limit: int = 10) -> pd.DataFrame:
    where, params = ("where release_year = ?", [year]) if year else ("", [])
    sql = MOVIE_FACTS_CTE + f"""
        select title, release_year, total_gross, imdb_rating
        from movie_facts
        {where}
        order by total_gross desc
        limit {limit}
    """
    return run_query(sql, params)


def best_word_of_mouth(year: int | None, wide_only: bool, limit: int = 10) -> pd.DataFrame:
    conditions, params = [], []
    if year:
        conditions.append("release_year = ?")
        params.append(year)
    if wide_only:
        conditions.append("is_wide_release")
    where = "where " + " and ".join(conditions) if conditions else ""
    sql = MOVIE_FACTS_CTE + f"""
        select title, release_year, total_gross, opening_week_gross, legs_multiplier
        from movie_facts
        {where}
        order by legs_multiplier desc
        limit {limit}
    """
    return run_query(sql, params)


def best_rated(year: int | None, min_votes: int, limit: int = 10) -> pd.DataFrame:
    conditions, params = ["imdb_votes >= ?"], [min_votes]
    if year:
        conditions.append("release_year = ?")
        params.append(year)
    where = "where " + " and ".join(conditions)
    sql = MOVIE_FACTS_CTE + f"""
        select title, release_year, imdb_rating, imdb_votes, total_gross
        from movie_facts
        {where}
        order by imdb_rating desc
        limit {limit}
    """
    return run_query(sql, params)


def rating_vs_revenue(min_votes: int) -> pd.DataFrame:
    sql = MOVIE_FACTS_CTE + """
        select title, release_year, imdb_rating, imdb_votes, total_gross
        from movie_facts
        where imdb_rating is not null and imdb_votes >= ?
    """
    return run_query(sql, [min_votes])
