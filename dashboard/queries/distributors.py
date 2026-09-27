"""Q2 (strongest openings), Q5 (market share over time).

R1 (wide releases only) and R3 (group ratios use sum / sum, not the average of
ratios) both apply here — see README section 3.
"""

import pandas as pd

from db import run_query
from queries.base import MOVIE_FACTS_CTE


def strongest_openings(year: int | None, limit: int = 10) -> pd.DataFrame:
    conditions, params = ["is_wide_release", "distributor_name is not null"], []
    if year:
        conditions.append("release_year = ?")
        params.append(year)
    where = "where " + " and ".join(conditions)
    sql = MOVIE_FACTS_CTE + f"""
        select
            distributor_name,
            sum(opening_week_gross) as total_opening_week_gross,
            sum(opening_theaters) as total_opening_theaters,
            sum(opening_week_gross) / nullif(sum(opening_theaters), 0) as opening_week_per_theater,
            count(*) as movie_count
        from movie_facts
        {where}
        group by distributor_name
        order by opening_week_per_theater desc
        limit {limit}
    """
    return run_query(sql, params)


def market_share_by_year(year_from: int, year_to: int) -> pd.DataFrame:
    sql = MOVIE_FACTS_CTE + """
        select
            release_year,
            distributor_name,
            sum(total_gross) as distributor_gross,
            sum(total_gross) * 1.0 / sum(sum(total_gross)) over (partition by release_year) as market_share
        from movie_facts
        where distributor_name is not null and release_year between ? and ?
        group by release_year, distributor_name
    """
    return run_query(sql, [year_from, year_to])
