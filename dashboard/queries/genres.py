"""Q6 (top-grossing movie per genre), Q7 (genres that earn the most).

R4 applies: a movie counts in every genre it has, so genre totals overlap
(a movie with 3 genres contributes its full total_gross to each).
"""

import pandas as pd

from db import run_query
from queries.base import MOVIE_FACTS_CTE


def top_movie_per_genre(year: int | None) -> pd.DataFrame:
    where, params = ("where mf.release_year = ?", [year]) if year else ("", [])
    sql = MOVIE_FACTS_CTE + f"""
        , genre_movies as (
            select
                mg.genre,
                mf.title,
                mf.release_year,
                mf.total_gross,
                row_number() over (partition by mg.genre order by mf.total_gross desc) as rnk
            from movie_facts mf
            join marts.movie_genre mg on mf.movie_key = mg.movie_key
            {where}
        )
        select genre, title, release_year, total_gross
        from genre_movies
        where rnk = 1
        order by total_gross desc
    """
    return run_query(sql, params)


def genre_totals(year: int | None) -> pd.DataFrame:
    where, params = ("where mf.release_year = ?", [year]) if year else ("", [])
    sql = MOVIE_FACTS_CTE + f"""
        select mg.genre, sum(mf.total_gross) as total_gross, count(*) as movie_count
        from movie_facts mf
        join marts.movie_genre mg on mf.movie_key = mg.movie_key
        {where}
        group by mg.genre
        order by total_gross desc
    """
    return run_query(sql, params)
