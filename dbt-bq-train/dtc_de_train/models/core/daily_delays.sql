{{ config(materialized="table") }}

with movements as (select * from {{ ref("dim_movements") }})
select
    count(*) over (
        partition by variation_status, company_name order by company_name asc
    )
    / count(*) over (partition by company_name) as percentage_of_variation,
    variation_status,
    company_name,
from movements
group by 3, 4
