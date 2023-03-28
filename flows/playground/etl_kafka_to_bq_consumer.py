import csv
import json
import os
from datetime import date, datetime
from pathlib import Path
from random import randint
from time import sleep

import numpy as np
import pandas as pd
import prefect
import pyarrow as pa

# from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from prefect import flow, get_run_logger, task
from prefect.blocks.system import String
from prefect.filesystems import LocalFileSystem
from prefect.task_runners import ConcurrentTaskRunner, SequentialTaskRunner
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket
from pytz import timezone

# data map to /opt/prefect in docker container
loc = Path(__file__).parents[1] / "data"

TIMEZONE_LONDON: timezone = timezone("Europe/London")


# @task(log_prints=True)
# def write_local(df: pd.DataFrame, color: str, dataset_file: str) -> Path:
#     """Write DataFrame out locally as parquet file"""
#     parent = Path(f"{loc}/{color}")
#     if not Path.is_dir(parent):
#         parent.mkdir(parents=True, exist_ok=False)


#     path = Path(f"{parent}/{dataset_file}.parquet")
#     df.to_parquet(path, compression="gzip")
#     print(f"path is {path}")
#     return path
# @task(log_prints=True)
# def write_local(local_file, body, uk_datetime_str, toc_id):
#     filename = f"{uk_datetime_str}-{toc_id}.json"
#     with open(f"{local_file}/{filename}", "a") as f:
#         f.write(json.dumps(body))
#     return filename


@task()
def write_gcs(path: Path) -> None:
    """Upload local parquet file to GCS"""
    to_path = Path("data") / path.parent.name / path.name
    gcs_block = GcsBucket.load("dtc-project-gcs")
    gcs_block.upload_from_path(from_path=path, to_path=to_path)
    return


def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to BiqQuery"""

    gcp_credentials_block = GcpCredentials.load("dtc-de-project-cred")

    df.to_gbq(
        destination_table="train.movements",
        project_id="dtc-de-project-380810",
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


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


@flow()
def get_data(log_prints=True):
    today = date.today()

    # Getting the data as JSON
    consumer = KafkaConsumer(
        bootstrap_servers=["host.docker.internal:9092"],
        value_deserializer=lambda m: json.loads(m.decode("ascii")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="group_1",
        # consumer_timeout_ms=5000,
    )

    print("Consumer ready")

    topic = "TRAIN_MVT_ALL_TOC"

    # prepare consumer
    tp = TopicPartition(topic, 0)
    consumer.assign([tp])
    lastOffset = consumer.end_offsets([tp])[tp]
    print("lastOffset:", lastOffset)

    for message in consumer:
        lastOffset = consumer.end_offsets([tp])[tp]
        print("lastOffset:", lastOffset)
        response = message.value
        for info in response:
            header = info["header"]
            msg_type = header["msg_type"]
            body = info["body"]
            if msg_type == "0003":
                timestamp = int(body["actual_timestamp"]) / 1000
                utc_datetime = datetime.utcfromtimestamp(timestamp)
                uk_datetime = TIMEZONE_LONDON.fromutc(utc_datetime)
                uk_datetime_str = uk_datetime.strftime("%Y%m%d-%H%M%S")
                uk_date = uk_datetime.date()
                uk_year = uk_date.year
                uk_month = uk_date.month
                uk_day = uk_date.day
                toc_id = body["toc_id"]

                # filename = write_local(local_file, body, uk_datetime_str, toc_id)
                # print(f"body type is {type(body)}")
                # print(body)
                df = pd.DataFrame([body])
                print(df.iloc[0])
                clean_df = clean(df)
                write_bq(clean_df)

                # for reviwing the msssage
                # print(
                #     header["msg_type"],
                #     body["event_type"],
                #     body["toc_id"],
                #     body["variation_status"],
                #     uk_datetime,
                # )


# @flow
# def main():
#     get_data()


if __name__ == "__main__":
    get_data()
