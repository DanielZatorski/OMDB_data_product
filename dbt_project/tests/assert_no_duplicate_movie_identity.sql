-- Would have caught the "Jurassic World Dominion" vs "Jurassic World: Dominion"
-- bug directly: no two dim_movie rows should share the same (title, release_year).
select title, release_year, count(*) as row_count
from {{ ref('dim_movie') }}
group by title, release_year
having count(*) > 1
