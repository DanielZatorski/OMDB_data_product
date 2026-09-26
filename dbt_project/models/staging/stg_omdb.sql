select
    requested_title,
    trim(regexp_replace(lower(requested_title), '[^a-z0-9]+', ' ', 'g')) as title_key,
    requested_year,
    imdb_id,
    title as matched_title,
    year as matched_year,
    nullif(genre, 'N/A') as genre,
    nullif(imdb_rating, 'N/A')::double as imdb_rating,
    case
        when imdb_votes is null or imdb_votes = 'N/A' then null
        else cast(replace(imdb_votes, ',', '') as bigint)
    end as imdb_votes,
    response = 'True' as omdb_matched,
    error as error_message
from {{ source('raw', 'omdb_responses') }}
