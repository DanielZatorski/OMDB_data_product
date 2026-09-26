{{ config(severity='warn') }}

-- Fails (returns a row) if the OMDb match rate drops below 90%,
-- flagging a possible regression rather than the currently-known ~95%.
select
    count(*) as total,
    sum(case when omdb_matched then 1 else 0 end) as matched,
    round(100.0 * sum(case when omdb_matched then 1 else 0 end) / count(*), 1) as match_rate_pct
from {{ ref('stg_omdb') }}
having match_rate_pct < 90
