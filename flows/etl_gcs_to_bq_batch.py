import json
from io import BytesIO

import numpy as np
import pandas as pd
from prefect import flow, task
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket


@task(log_prints=True)
def list_blobs(bucket_name):
    """Lists all the blobs in the bucket"""
    # blobs = gcs_block.list_blobs(bucket_name)
    gcs_block = GcsBucket.load("dtc-de-project")
    return gcs_block.list_blobs(bucket_name)


@task(retries=0, log_prints=True)
def extrct_from_gcs(file):
    gcs_block = GcsBucket.load("dtc-de-project")
    with BytesIO() as buf:
        gcs_block.download_object_to_file_object(
            # "train_mov/20230322-001500-29.json", buf
            file,
            buf,
        )
        buf.seek(0)  # move to the beginning of the file

        df = pd.DataFrame.from_dict(json.loads(str(buf.read(), "utf-8")))
        return df


@task()
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix data type issue: "pandas_gbq.exceptions.ConversionError: Could not convert Dataframe to Parquet"""
    df.replace("", np.nan, inplace=True)
    df_clean = df.astype(
        {
            "event_type": "string",
            "gbtt_timestamp": "string",
            "original_loc_stanox": "string",
            "planned_timestamp": "Int64",
            "timetable_variation": "Int64",
            "original_loc_timestamp": "string",
            "current_train_id": "string",
            "delay_monitoring_point": "string",
            "next_report_run_time": "Int64",
            "reporting_stanox": "Int64",
            "actual_timestamp": "Int64",
            "correction_ind": "string",
            "event_source": "string",
            "train_file_address": "string",
            "platform": "string",
            "division_code": "Int64",
            "train_terminated": "string",
            "train_id": "string",
            "offroute_ind": "string",
            "variation_status": "string",
            "train_service_code": "Int64",
            "toc_id": "Int64",
            "loc_stanox": "Int64",
            "auto_expected": "string",
            "direction_ind": "string",
            "route": "Int64",
            "planned_event_type": "string",
            "next_report_stanox": "Int64",
            "line_ind": "string",
        },
        errors="ignore",
    )
    return df_clean


@task()
def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to BiqQuery"""

    gcp_credentials_block = GcpCredentials.load("dtc-de-project-cred")

    df.to_gbq(
        destination_table="ext_train.movements",
        project_id="dtc-de-project-380810",
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


@flow()
def etl_gcs_to_bq():
    blobs = list_blobs("")
    for blob in blobs:
        file = blob.name.replace("data/", "")
        try:
            df = extrct_from_gcs(file)
            write_bq(clean(df))
        except ValueError:
            print(f"Can't process {file}")


if __name__ == "__main__":
    etl_gcs_to_bq()
