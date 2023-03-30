import sys
from pathlib import Path
from time import sleep
from typing import Dict, List

parent_directory = Path(__file__).resolve().parents[1]
sys.path.append(str(parent_directory / "utilities"))
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import MessageField, SerializationContext
from train_record import TrainRecord, train_record_to_dict
from train_record_key import TrainRecordKey, train_record_key_to_dict


class TrainAvroProducer:
    def __init__(self, props: Dict):
        # Schema Registry and Serializer-Deserializer Configurations
        key_schema_str = self.load_schema(props["schema.key"])
        value_schema_str = self.load_schema(props["schema.value"])
        schema_registry_props = {"url": props["schema_registry.url"]}
        schema_registry_client = SchemaRegistryClient(schema_registry_props)
        self.key_serializer = AvroSerializer(
            schema_registry_client, key_schema_str, train_record_key_to_dict
        )
        self.value_serializer = AvroSerializer(
            schema_registry_client, value_schema_str, train_record_to_dict
        )

        # Producer Configuration
        producer_props = {"bootstrap.servers": props["bootstrap.servers"]}
        self.producer = Producer(producer_props)

    @staticmethod
    def load_schema(schema_path: str):
        # path = os.path.realpath(os.path.dirname(__file__))
        # with open(f"{path}/{schema_path}") as f:
        with open(f"{schema_path}") as f:
            schema_str = f.read()
        return schema_str

    @staticmethod
    def delivery_report(err, msg):
        if err is not None:
            print("Delivery failed for record {}: {}".format(msg.key(), err))
            return
        print(
            "Record {} successfully produced to {} [{}] at offset {}".format(
                msg.key(), msg.topic(), msg.partition(), msg.offset()
            )
        )

    @staticmethod
    def read_records(reader: list):
        train_records, train_keys = [], []
        for row in reader:
            train_records.append(TrainRecord.from_dict(row))
            train_keys.append(TrainRecordKey.from_dict(row))
        return zip(train_keys, train_records)

    def publish(self, topic: str, records: [TrainRecordKey, TrainRecord]):
        for key_value in records:
            key, value = key_value
            try:
                self.producer.produce(
                    topic=topic,
                    key=self.key_serializer(
                        key, SerializationContext(topic=topic, field=MessageField.KEY)
                    ),
                    value=self.value_serializer(
                        value,
                        SerializationContext(topic=topic, field=MessageField.VALUE),
                    ),
                    on_delivery=delivery_report,
                )
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Exception while producing record - {value}: {e}")

        self.producer.flush()
        sleep(10)


def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed for record {}: {}".format(msg.key(), err))
        return
    print(
        "Record {} successfully produced to {} [{}] at offset {}".format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()
        )
    )
