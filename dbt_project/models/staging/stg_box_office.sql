select
    id,
    title,
    -- normalized for joining/grouping only — the same movie can appear under
    -- slightly different title spellings (e.g. "Jurassic World Dominion" vs
    -- "Jurassic World: Dominion"); this merges those back together
    trim(regexp_replace(lower(title), '[^a-z0-9]+', ' ', 'g')) as title_key,
    date,
    revenue,
    theaters,
    nullif(distributor, '-') as distributor,
    release_year
from {{ source('raw', 'box_office') }}
