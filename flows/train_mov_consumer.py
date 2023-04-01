import json
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List

from prefect_gcp.cloud_storage import GcsBucket

parent_directory = Path(__file__).resolve().parents[2]
sys.path.append(str(parent_directory / "utilities"))
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import MessageField, SerializationContext
from pytz import timezone
from train_record import dict_to_train_record, train_record_to_dict
from train_record_key import dict_to_train_record_key

loc = Path(__file__).parents[1] / "data"

TIMEZONE_LONDON: timezone = timezone("Europe/London")
GCS_BUCKET = gcs_block = GcsBucket.load("dtc-de-project")
GCS_PATH = "train_mov"


class TrainAvroConsumer:
    def __init__(self, props: Dict):
        # Schema Registry and Serializer-Deserializer Configurations
        key_schema_str = self.load_schema(props["schema.key"])
        value_schema_str = self.load_schema(props["schema.value"])
        schema_registry_props = {"url": props["schema_registry.url"]}
        schema_registry_client = SchemaRegistryClient(schema_registry_props)
        self.avro_key_deserializer = AvroDeserializer(
            schema_registry_client=schema_registry_client,
            schema_str=key_schema_str,
            from_dict=dict_to_train_record_key,
        )
        self.avro_value_deserializer = AvroDeserializer(
            schema_registry_client=schema_registry_client,
            schema_str=value_schema_str,
            from_dict=dict_to_train_record,
        )

        consumer_props = {
            "bootstrap.servers": props["bootstrap.servers"],
            "group.id": "dtc_de_project.train_movements.avro.consumer.2",
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(consumer_props)

    @staticmethod
    def load_schema(schema_path: str):
        # path = os.path.realpath(os.path.dirname(__file__))
        with open(f"{schema_path}") as f:
            schema_str = f.read()
        return schema_str

    def consume_from_kafka(self, topics: List[str]):
        self.consumer.subscribe(topics=topics)
        results = []
        while True:
            try:
                # SIGINT can't be handled when polling, limit timeout to 1 second.
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                key = self.avro_key_deserializer(
                    msg.key(), SerializationContext(msg.topic(), MessageField.KEY)
                )
                record = self.avro_value_deserializer(
                    msg.value(), SerializationContext(msg.topic(), MessageField.VALUE)
                )
                if record is not None:
                    print("{}, {}".format(key, record))
                    body = train_record_to_dict(record)
                    results.append(body)
                    uk_datetime_str, toc_id = self.parse_msg(body)

                    # Write to local
                    # self.write_local(loc, body, uk_datetime_str, toc_id)

                    # Write to gcs
                    self.write_msg_to_gcs(body, uk_datetime_str, toc_id)
            except KeyboardInterrupt:
                break

        self.consumer.close()
        return results

    def write_msg_to_gcs(self, body, uk_datetime_str, toc_id):
        buf = BytesIO(json.dumps([body]).encode("utf-8"))
        gcs_path = GCS_BUCKET.upload_from_file_object(
            buf,
            f"{GCS_PATH}/{toc_id}/{uk_datetime_str}-{toc_id}.json",
        )
        print(f"file written to {gcs_path}")
        return gcs_path

    def parse_msg(self, message):
        timestamp = int(message["actual_timestamp"]) / 1000
        utc_datetime = datetime.utcfromtimestamp(timestamp)
        uk_datetime = TIMEZONE_LONDON.fromutc(utc_datetime)
        uk_datetime_str = uk_datetime.strftime("%Y%m%d-%H%M%S")
        toc_id = message["toc_id"]
        return (uk_datetime_str, toc_id)

    def write_local(self, local_file, body, uk_datetime_str, toc_id):
        filename = f"{uk_datetime_str}-{toc_id}.json"
        file_path = f"{local_file}/{filename}"
        with open(file_path, "a") as f:
            f.write(json.dumps([body]))
        path = Path(file_path)
        print(f"filename is {path}")
        return path
