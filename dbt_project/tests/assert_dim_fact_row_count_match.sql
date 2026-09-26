-- Grain of fact_movie_performance is "one row per movie" (README section 6),
-- so it must have exactly as many rows as dim_movie — no movie missing, none
-- duplicated.
select
    (select count(*) from {{ ref('dim_movie') }}) as dim_movie_count,
    (select count(*) from {{ ref('fact_movie_performance') }}) as fact_count
where (select count(*) from {{ ref('dim_movie') }})
    != (select count(*) from {{ ref('fact_movie_performance') }})
