import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

query = "select count(*) from `dtc-de-project-380810.train.dim_movements` limit 1 "
# bq = bigquery.Client(credentials=gcp_credentials_block)
# GCS_BUCKET = GcsBucket.load("dtc-de-project")


@st.cache_data(ttl=600)
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    rows = [dict(row) for row in rows_raw]
    return rows


rows = run_query(query)
# Print results.
print(rows)
st.write(rows)
# # st.write("Some wise words from Shakespeare:")
# # for row in rows:
# #     st.write("✍️ " + row['word'])


# with bq as warehouse:
#     operation = """
#         select * from `dtc-de-project-380810.ext_train.movements` limit 2
#     """
#     # parameters = {
#     #     "corpus": "romeoandjuliet",
#     #     "min_word_count": 250,
#     # }
#     result = warehouse.fetch_all(operation)
#     print(type(result[0]))

# df = bigquery_query(query, to_dataframe=True, gcp_credentials=gcp_credentials_block)
# print(df)
