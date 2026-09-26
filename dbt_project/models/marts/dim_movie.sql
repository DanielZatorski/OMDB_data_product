-- Grain: one row per movie. Built straight from stg_omdb, which already has
-- exactly one row per selected movie (950) under its canonical title.
select
    row_number() over (order by requested_title, requested_year) as movie_key,
    requested_title as title,
    requested_year as release_year,
    imdb_id,
    omdb_matched
from {{ ref('stg_omdb') }}
