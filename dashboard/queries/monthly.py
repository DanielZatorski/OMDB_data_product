"""Q4: which release month gives the biggest openings."""

import pandas as pd

from db import run_query
from queries.base import MOVIE_FACTS_CTE


def openings_by_month(wide_only: bool = True) -> pd.DataFrame:
    where = "where is_wide_release" if wide_only else ""
    sql = MOVIE_FACTS_CTE + f"""
        select
            release_month,
            release_month_name,
            sum(opening_week_gross) as total_opening_week_gross,
            avg(opening_week_gross) as avg_opening_week_gross,
            count(*) as movie_count
        from movie_facts
        {where}
        group by release_month, release_month_name
        order by release_month
    """
    return run_query(sql)
