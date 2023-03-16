import csv
import json
import os
from datetime import date, datetime
from pathlib import Path
from random import randint
from time import sleep

import pandas as pd
import prefect
# from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from prefect import flow, get_run_logger, task
from prefect.blocks.system import String
from prefect.filesystems import LocalFileSystem
from prefect.task_runners import ConcurrentTaskRunner, SequentialTaskRunner
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
@task(log_print=True)
def write_local(local_file, body, uk_datetime_str, toc_id):
    filename = f"{uk_datetime_str}-{toc_id}.json"
    with open(f"{local_file}/{filename}", "a") as f:
        f.write(json.dumps(body))
    return filename

@task()
def write_gcs(path: Path) -> None:
    """Upload local parquet file to GCS"""
    to_path = Path('data') / path.parent.name / path.name
    gcs_block = GcsBucket.load("dtc-project-gcs")
    gcs_block.upload_from_path(from_path=path, to_path=to_path)
    return

@flow
def get_data(log_prints=True):
    
    today = date.today()

    # Getting the data as JSON
    consumer = KafkaConsumer(
        bootstrap_servers=['host.docker.internal:9092'],
        value_deserializer=lambda m: json.loads(m.decode('ascii')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='group_1',
        #consumer_timeout_ms=5000,
        )

    print("Consumer ready")

    topic = 'TRAIN_MVT_ALL_TOC'

    # prepare consumer
    tp = TopicPartition(topic,0)
    consumer.assign([tp])
    lastOffset = consumer.end_offsets([tp])[tp]
    print("lastOffset:",lastOffset)

    # Local file path retrived from Prefect Local File System (which can be created on Prefect UI)
    local_file = "/opt/prefect/data"

    csv_columns = [ "event_type",
    "gbtt_timestamp",
    "original_loc_stanox",
    "planned_timestamp",
    "timetable_variation",
    "original_loc_timestamp",
    "current_train_id",
    "delay_monitoring_point",
    "next_report_run_time",
    "reporting_stanox",
    "actual_timestamp",
    "correction_ind",
    "event_source",
    "train_file_address",
    "platform",
    "division_code",
    "train_terminated",
    "train_id",
    "offroute_ind",
    "variation_status",
    "train_service_code",
    "toc_id",
    "loc_stanox",
    "auto_expected",
    "direction_ind",
    "route",
    "planned_event_type",
    "next_report_stanox",
    "line_ind"]

    for message in consumer:
        lastOffset = consumer.end_offsets([tp])[tp]
        print("lastOffset:",lastOffset)
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

                filename = write_local(local_file, body, uk_datetime_str, toc_id)

                # for reviwing the msssage
                print(
                    header["msg_type"],
                    body["event_type"],
                    body["toc_id"],
                    body["variation_status"],
                    uk_datetime,
                )


@flow
def main():
    get_data()
    
if __name__=="__main__":
    main()