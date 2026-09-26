select *
from {{ ref('stg_box_office') }}
where revenue < 0
