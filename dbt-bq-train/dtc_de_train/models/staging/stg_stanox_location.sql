{{ config(materialized="view") }}

with stanox_location as (select * from {{ source("seeding", "ukrail_locations") }})
select *
from stanox_location
