import csv
import json
import os
import pathlib
import sys
from datetime import date, datetime
from pathlib import Path
from random import randint
from time import sleep
from typing import Dict, List

parent_directory = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(parent_directory / "utilities"))
import pandas as pd
import prefect

# from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from prefect import flow, get_run_logger, task
from prefect.blocks.system import String
from prefect.filesystems import LocalFileSystem
from prefect.task_runners import ConcurrentTaskRunner, SequentialTaskRunner
from prefect_gcp.cloud_storage import GcsBucket
from settings import (
    BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    SCHEMA_REGISTRY_URL,
    TRAIN_KEY_SCHEMA_PATH,
    TRAIN_VALUE_SCHEMA_PATH,
)
from train_mov_consumer import TrainAvroConsumer

# data map to /opt/prefect in docker container
# loc = Path(__file__).parents[1] / "data"

# TIMEZONE_LONDON: timezone = timezone("Europe/London")


@task(log_prints=True)
def write_local(local_file, body, uk_datetime_str, toc_id):
    filename = f"{uk_datetime_str}-{toc_id}.json"
    file_path = f"{local_file}/{filename}"
    with open(file_path, "a") as f:
        f.write(json.dumps([body]))
    path = Path(file_path)
    print(f"filename is {path}")
    return path


@task()
def write_gcs(path: Path) -> None:
    """Upload local parquet file to GCS"""
    to_path = Path("train_mov") / path.name
    gcs_block = GcsBucket.load("dtc-de-project")
    # gcs_block = GcsBucket.load("dtc-project-gcs")
    gcs_block.upload_from_path(from_path=path, to_path=to_path)
    return


@flow(log_prints=True)
def consume_data(config: Dict):
    avro_consumer = TrainAvroConsumer(props=config)
    avro_consumer.consume_from_kafka(topics=["train_movements"])
    # record, messages = avro_consumer.consume_from_kafka(topics=["train_movements"])
    # # while True:
    # for message in messages:
    #     print(type(message))
    #     return message


@flow(log_prints=True)
def get_data():
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

    # Local file path retrived from Prefect Local File System (which can be created on Prefect UI)
    local_file = "/opt/prefect/data"

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

                filename = write_local(local_file, body, uk_datetime_str, toc_id)
                write_gcs(filename)

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
    # get_data()
    config = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "schema_registry.url": SCHEMA_REGISTRY_URL,
        "schema.key": TRAIN_KEY_SCHEMA_PATH,
        "schema.value": TRAIN_VALUE_SCHEMA_PATH,
    }
    result = consume_data(config)
    # write_gcs(write_local(consume_data(config)))


if __name__ == "__main__":
    main()
