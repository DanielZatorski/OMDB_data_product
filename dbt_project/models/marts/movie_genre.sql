-- Bridge table: genre is multi-valued (OMDb's Genre is comma-separated), so a
-- movie can have several rows here — one per genre (README rule R4).
select
    dm.movie_key,
    trim(unnest(string_split(so.genre, ','))) as genre
from {{ ref('stg_omdb') }} so
inner join {{ ref('dim_movie') }} dm
    on so.requested_title = dm.title
    and so.requested_year = dm.release_year
where so.genre is not null
