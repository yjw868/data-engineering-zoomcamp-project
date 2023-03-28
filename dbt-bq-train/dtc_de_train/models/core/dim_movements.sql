{{ config(materialized="table") }}

with
    movements as (select * from {{ ref("stg_movements") }}),
    rail_loc_code as (select * from {{ ref("stg_rail_loc_code") }}),
    transformation as (
        select
            event_type,
            timestamp_seconds(
                div(cast(gbtt_timestamp as integer), 1000)
            ) as gbtt_timestamp,
            original_loc_stanox,
            timestamp_seconds(
                div(cast(planned_timestamp as integer), 1000)
            ) as planned_timestamp,
            timetable_variation,
            timestamp_seconds(
                div(cast(original_loc_timestamp as integer), 1000)
            ) as original_loc_timestamp,
            current_train_id,
            cast(delay_monitoring_point as boolean) as delay_monitoring_point,
            next_report_run_time,
            reporting_stanox,
            timestamp_seconds(
                div(cast(actual_timestamp as integer), 1000)
            ) as actual_timestamp,
            cast(correction_ind as boolean) as correction_ind,
            event_source,
            train_file_address,
            platform,
            division_code,
            cast(train_terminated as boolean) as train_terminated,
            train_id,
            cast(offroute_ind as boolean) as offroute_ind,
            variation_status,
            train_service_code,
            toc_id,
            loc_stanox,
            auto_expected,
            direction_ind,
            route,
            planned_event_type,
            next_report_stanox,
            line_ind
        from movements
    ),
    final as (
        select t.*, r.description as original_loc, loc.description as loc
        from transformation t
        left join rail_loc_code r on t.original_loc_stanox = r.stannox
        left join rail_loc_code loc on t.loc_stanox = loc.stannox
    )
select *
from final
