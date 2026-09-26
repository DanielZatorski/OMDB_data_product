-- total_gross can never be less than opening_week_gross (the opening week's
-- revenue is a subset of the total run) — a violation means the aggregation
-- in int_movie_performance is broken.
select *
from {{ ref('fact_movie_performance') }}
where total_gross < opening_week_gross
