{{ config(materialized="view") }}

with toc as (select * from {{ source("seeding", "toc") }})
select *
from toc
