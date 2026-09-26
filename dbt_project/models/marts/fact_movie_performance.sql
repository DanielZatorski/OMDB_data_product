-- Grain: one row per movie (title + release year). Market share % is not
-- stored here — it's calculated at query time (README section 2), since its
-- value depends on the dashboard's active filters.
select
    dm.movie_key,
    dd.distributor_key,
    ddt.date_key as release_date_key,
    mp.opening_theaters,
    mp.is_wide_release,
    mp.total_gross,
    mp.opening_week_gross,
    mp.opening_week_per_theater,
    mp.legs_multiplier,
    so.imdb_rating,
    so.imdb_votes
from {{ ref('int_movie_performance') }} mp
inner join {{ ref('stg_omdb') }} so
    on mp.title_key = so.title_key
    and mp.release_year = so.requested_year
inner join {{ ref('dim_movie') }} dm
    on so.requested_title = dm.title
    and so.requested_year = dm.release_year
left join {{ ref('dim_distributor') }} dd
    on mp.distributor = dd.distributor_name
left join {{ ref('dim_date') }} ddt
    on mp.release_date = ddt.date
