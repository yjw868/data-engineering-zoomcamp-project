import pathlib
import sys
from time import sleep
from typing import Dict, List

parent_directory = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(parent_directory / "utilities"))

from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from settings import (
    BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    SCHEMA_REGISTRY_URL,
    TRAIN_KEY_SCHEMA_PATH,
    TRAIN_VALUE_SCHEMA_PATH,
)
from train_mov_consumer import TrainAvroConsumer


@task(log_prints=True)
def consume_data(config: Dict):
    avro_consumer = TrainAvroConsumer(props=config)
    results = avro_consumer.consume_from_kafka(topics=["train_movements"])
    print(results)


@flow
def etl_kafka_to_gcs():
    # get_data()
    config = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "schema_registry.url": SCHEMA_REGISTRY_URL,
        "schema.key": TRAIN_KEY_SCHEMA_PATH,
        "schema.value": TRAIN_VALUE_SCHEMA_PATH,
    }
    consume_data(config)


if __name__ == "__main__":
    etl_kafka_to_gcs()
