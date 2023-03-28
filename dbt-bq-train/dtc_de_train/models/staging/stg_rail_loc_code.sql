{{ config(materialized="view") }}

with
    rail_loc_code as (

        select crs, tiploc, description, safe_cast(stannox as integer) as stannox
        from {{ source("staging", "rail_loc_code") }}

    )
select *
from rail_loc_code
