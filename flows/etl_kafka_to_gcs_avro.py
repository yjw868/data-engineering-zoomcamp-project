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
    results = avro_consumer.consume_from_kafka(topics=["train_movements"])
    print(results)


@flow
def main():
    # get_data()
    config = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "schema_registry.url": SCHEMA_REGISTRY_URL,
        "schema.key": TRAIN_KEY_SCHEMA_PATH,
        "schema.value": TRAIN_VALUE_SCHEMA_PATH,
    }
    consume_data(config)
    # write_gcs(write_local(consume_data(config)))


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


# @task()
# def write_gcs(path: Path) -> None:
#     """Upload local parquet file to GCS"""
#     to_path = Path("train_mov") / path.name
#     gcs_block = GcsBucket.load("dtc-de-project")
#     # gcs_block = GcsBucket.load("dtc-project-gcs")
#     gcs_block.upload_from_path(from_path=path, to_path=to_path)
#     return


@flow(log_prints=True)
def consume_data(config: Dict):
    avro_consumer = TrainAvroConsumer(props=config)
    results = avro_consumer.consume_from_kafka(topics=["train_movements"])
    print(results)


@flow
def etl_kafka_to_local():
    # get_data()
    config = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "schema_registry.url": SCHEMA_REGISTRY_URL,
        "schema.key": TRAIN_KEY_SCHEMA_PATH,
        "schema.value": TRAIN_VALUE_SCHEMA_PATH,
    }
    consume_data(config)
    # write_gcs(write_local(consume_data(config)))


if __name__ == "__main__":
    etl_kafka_to_local()

if __name__ == "__main__":
    main()
