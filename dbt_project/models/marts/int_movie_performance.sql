-- Intermediate: one row per movie (title_key + release_year) with the box-office
-- KPIs from README section 2. Feeds fact_movie_performance, dim_distributor, and
-- dim_date, so each of those sees the same opening-day/release-date per movie.

with box_office as (
    select *
    from {{ ref('stg_box_office') }}
),

movie_release as (
    select
        title_key,
        release_year,
        min(date) as release_date
    from box_office
    group by title_key, release_year
),

opening_day as (
    select
        b.title_key,
        b.release_year,
        b.theaters as opening_theaters,
        b.distributor
    from box_office b
    inner join movie_release r
        on b.title_key = r.title_key
        and b.release_year = r.release_year
        and b.date = r.release_date
    qualify row_number() over (partition by b.title_key, b.release_year order by b.revenue desc) = 1
),

totals as (
    select
        b.title_key,
        b.release_year,
        sum(b.revenue) as total_gross,
        sum(case when b.date < r.release_date + interval 7 day then b.revenue else 0 end) as opening_week_gross
    from box_office b
    inner join movie_release r
        on b.title_key = r.title_key
        and b.release_year = r.release_year
    group by b.title_key, b.release_year
)

select
    t.title_key,
    t.release_year,
    r.release_date,
    o.distributor,
    o.opening_theaters,
    o.opening_theaters >= 600 as is_wide_release,
    t.total_gross,
    t.opening_week_gross,
    round(t.opening_week_gross / nullif(o.opening_theaters, 0), 2) as opening_week_per_theater,
    round(t.total_gross / nullif(t.opening_week_gross, 0), 2) as legs_multiplier
from totals t
inner join movie_release r on t.title_key = r.title_key and t.release_year = r.release_year
inner join opening_day o on t.title_key = o.title_key and t.release_year = o.release_year
