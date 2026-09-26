-- Grain: one row per distributor. Sourced from int_movie_performance (each
-- selected movie's opening-day distributor), not directly from stg_box_office,
-- so this only contains distributors actually tied to a selected movie.
select
    row_number() over (order by distributor) as distributor_key,
    distributor as distributor_name
from (
    select distinct distributor
    from {{ ref('int_movie_performance') }}
    where distributor is not null
)
