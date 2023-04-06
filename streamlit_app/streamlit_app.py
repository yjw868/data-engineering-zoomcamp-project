import datetime
import time

import pandas as pd
import plotly.express as px
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

epoch_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
st.set_page_config(layout="wide")

######################################################################
# Option to query BigQuery:
# You can also copy paste the dbt complied dim_movements sql below to
# query BigQuery
######################################################################
#
# credentials = service_account.Credentials.from_service_account_info(
#     st.secrets["gcp_service_account"]
# )
# client = bigquery.Client(credentials=credentials)

# # query = "select * from `dtc-de-project-380810.train.dim_movements` limit 2 "


# query = """
# with
#     movements as (select * from `dtc-de-project-380810`.`train`.`stg_movements`),
#     rail_loc_code as (select * from `dtc-de-project-380810`.`train`.`stg_rail_loc_code`),
#     toc as (select * from `dtc-de-project-380810`.`train`.`stg_toc`),
#     stanox_location as (select * from `dtc-de-project-380810`.`train`.`stg_stanox_location`),
#     transformation as (
#         select
#             event_type,
#             timestamp_seconds(
#                 div(cast(gbtt_timestamp as integer), 1000)
#             ) as gbtt_timestamp,
#             original_loc_stanox,
#             timestamp_seconds(
#                 div(cast(planned_timestamp as integer), 1000)
#             ) as planned_timestamp,
#             timetable_variation,
#             timestamp_seconds(
#                 div(cast(original_loc_timestamp as integer), 1000)
#             ) as original_loc_timestamp,
#             current_train_id,
#             cast(delay_monitoring_point as boolean) as delay_monitoring_point,
#             next_report_run_time,
#             reporting_stanox,
#             timestamp_seconds(
#                 div(cast(actual_timestamp as integer), 1000)
#             ) as actual_timestamp,
#             cast(correction_ind as boolean) as correction_ind,
#             event_source,
#             train_file_address,
#             platform,
#             division_code,
#             cast(train_terminated as boolean) as train_terminated,
#             train_id,
#             cast(offroute_ind as boolean) as offroute_ind,
#             variation_status,
#             train_service_code,
#             toc_id,
#             loc_stanox,
#             auto_expected,
#             direction_ind,
#             route,
#             planned_event_type,
#             next_report_stanox,
#             line_ind
#         from movements
#     ),
#     final as (
#         select
#             t.*,
#             r.description as original_loc,
#             loc.description as loc,
#             ifnull(toc.company_name, "unmapped") as company_name,
#             s.latitude as latitude,
#             s.longitude as longitude
#         from transformation t
#         left join
#             rail_loc_code r
#             on t.original_loc_stanox = r.stannox
#             and t.original_loc_stanox <> 0
#         left join rail_loc_code loc on t.loc_stanox = loc.stannox
#         left join toc on t.toc_id = toc.toc and t.toc_id <> 0
#         left join stanox_location s on s.stanox = t.loc_stanox
#     )
# select *
# from final
# """


# @st.cache_data(ttl=600)
# def run_query(query):
#     query_job = client.query(query)
#     rows_raw = query_job.result()
#     rows = [dict(row) for row in rows_raw]
#     return rows


# rows = run_query(query)
# df = pd.DataFrame(rows)

######################################################################
# Option to user exported parquet file
######################################################################
df = pd.read_parquet("dim_movements.parquet")


######################################################################
# Ploting the dashboard
######################################################################

df["planned_timestamp"] = df["planned_timestamp"].astype("datetime64")
start_date, end_date = df[df["planned_timestamp"] > epoch_time][
    "planned_timestamp"
].agg(["min", "max"])
st.write(
    f"This dashboard shows how the UK NetworkRail Operator perform between {start_date:%d-%m-%Y} and {end_date:%d-%m-%Y }"
)
df_variation_status = (
    df.groupby(by=["variation_status"])
    .agg(variation_status_count=("variation_status", "count"))
    .reset_index()
)

st.write(df_variation_status)
fig1 = px.pie(
    df_variation_status,
    values="variation_status_count",
    names="variation_status",
    title="A breakdown of train schedule by variation status",
    width=800,
    height=700,
)


df_variation_status_by_co = (
    df.groupby(by=["company_name", "variation_status"])
    .agg(variation_status_count=("variation_status", "count"))
    .reset_index()
)

# ordered_co_name = df_variation_status_by_co.sort_values(
#     by=["variation_status_count", "variation_status"]
# )["company_name"].to_list()

fig2 = px.bar(
    df_variation_status_by_co,
    x="company_name",
    y="variation_status_count",
    color="variation_status",
    title="A breakdown of train schedule by company and variation status",
    width=800,
    height=700,
)

# Sort chart data order
fig2.update_layout(barmode="stack", xaxis={"categoryorder": "total descending"})

# The chart was squashed, use this hack to display it properly
col1, _, col3, _ = st.columns(4)
with col1:
    st.plotly_chart(fig1)
with col3:
    st.plotly_chart(fig2)
