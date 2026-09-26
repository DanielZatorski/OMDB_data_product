-- Grain: one row per distinct release date across the selected movies (not a
-- full calendar range — only the dates fact_movie_performance actually needs).
select
    row_number() over (order by release_date) as date_key,
    release_date as date,
    extract(year from release_date) as year,
    extract(month from release_date) as month,
    strftime(release_date, '%B') as month_name
from (
    select distinct release_date
    from {{ ref('int_movie_performance') }}
)
