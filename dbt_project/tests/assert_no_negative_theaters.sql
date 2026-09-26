select *
from {{ ref('stg_box_office') }}
where theaters < 0
