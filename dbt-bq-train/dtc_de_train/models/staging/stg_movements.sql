{{ config(
    materialized = 'view'
) }}

with movdata as (

    select
        *,
        row_number() over(
            partition by train_id, actual_timestamp
        ) as rn
    from
        {{ source(
            'staging',
            'movements'
        ) }}

)
select
    -- identifiers
    {{ dbt_utils.generate_surrogate_key(['train_id', 'actual_timestamp']) }} as trainid,
    
    *
from
    movdata
where
    rn = 1 