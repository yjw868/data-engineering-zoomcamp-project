import json
from io import BytesIO, StringIO

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
def extract_from_gcs(gcs_block, file):
    """Extract file contents from gcs

    Args:
        gcs_block (prefect gcs block): Predefined in Prefect Orion
        file (string): blob name eg. "train_mov/20230322-001500-29.json"

    Returns:
        string: contents of the blo
    """
    with BytesIO() as buf:
        gcs_block.download_object_to_file_object(
            file,
            buf,
        )
        buf.seek(0)  # move to the beginning of the file
        contents = buf.read().decode("ISO-8859-1")
        return contents


@task()
def clean(contents: str) -> pd.DataFrame:
    """Fix data type issue: "pandas_gbq.exceptions.ConversionError: Could not convert Dataframe to Parquet"""
    try:
        df = pd.DataFrame.from_dict(json.loads(contents))
        df.replace("", np.nan, inplace=True)
        df_clean = df.astype(
            {
                "event_type": "string",
                "gbtt_timestamp": "Int64",
                "original_loc_stanox": "Int64",
                "planned_timestamp": "Int64",
                "timetable_variation": "Int64",
                "original_loc_timestamp": "Int64",
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
    except ValueError:
        return 0


@task()
def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to BiqQuery"""

    gcp_credentials_block = GcpCredentials.load("dtc-de-project-cred")
    if type(df) == pd.DataFrame:
        try:
            df.to_gbq(
                destination_table="ext_train.movements",
                project_id="dtc-de-project-380810",
                credentials=gcp_credentials_block.get_credentials_from_service_account(),
                chunksize=500_000,
                if_exists="append",
            )
        except ValueError:
            return 0


@flow(log_prints=True)
def list_files_to_ingest(gcs_block):
    """Find the list of files to ingest"""
    blobs = list_blobs("train_mov/")
    blobs_names = [blob.name for blob in blobs]
    df_blobs_name = pd.DataFrame(blobs_names, columns=["name"])

    file_ingested = extract_from_gcs(gcs_block, "files_ingested_to_bq.csv")
    # print(type(file_ingested))
    df_file_ingested = pd.read_csv(StringIO(file_ingested))
    delta = set(df_blobs_name["name"].to_list()).symmetric_difference(
        set(df_file_ingested["name"].to_list())
    )

    # Update the list
    # TODO this should based on actul files have been sucessfully ingested
    gcs_block.upload_from_dataframe(
        df=df_blobs_name, to_path="files_ingested_to_bq.csv", serialization_format="csv"
    )
    return list(delta)


@flow(log_prints=True)
def etl_gcs_to_bq():
    gcs_block = GcsBucket.load("dtc-de-project")
    files_to_ingest = list_files_to_ingest(gcs_block)
    print(files_to_ingest)

    if len(files_to_ingest) > 0:
        print("New files to ingest")
        for file in files_to_ingest:
            path = file.replace("data/", "")
            try:
                print(f"Ingesting {path}")
                write_bq(clean(extract_from_gcs(gcs_block, path)))
                print(f"{path} is uploaded")
            except ValueError:
                print(f"Can't process {path}")

    else:
        print("No new file to ingest")


if __name__ == "__main__":
    etl_gcs_to_bq()
