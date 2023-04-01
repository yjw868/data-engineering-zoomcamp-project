{{ config(materialized="view") }}

with
    movdata as (

        select *, row_number() over (partition by train_id, planned_timestamp) as rn
        from {{ source("staging", "movements") }}
    {# where train_id = '152D94M829' and planned_timestamp = 1680128580000 #}
    )
select
    -- identifiers
    {{ dbt_utils.generate_surrogate_key(["train_id", "planned_timestamp"]) }}
    as trainid,

    *
from movdata
where rn = 1
