import json
import os
import socket
from datetime import datetime
from time import sleep
from typing import Dict

import stomp
import toml
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import MessageField, SerializationContext
from pytz import timezone
from train_record import TrainRecord, train_record_to_dict
from train_record_key import TrainRecordKey, train_record_key_to_dict

with open("../secrets.toml", "r") as f:
    secrets = toml.load(f)

TIMEZONE_LONDON: timezone = timezone("Europe/London")

# Message type
MESSAGES = {
    "0001": "activation",
    "0002": "cancellation",
    "0003": "movement",
    "0004": "_unidentified",
    "0005": "reinstatement",
    "0006": "origin change",
    "0007": "identity change",
    "0008": "_location change",
}
# Datafeeds for information on the Open Data available from the rail industry in Great Britain
HOSTNAME = "datafeeds.networkrail.co.uk"


# def create_producer():
#     # topic = "public.networkrail.movement"
#     conf = {
#         "bootstrap.servers": "host.docker.internal:9092",
#         "client.id": socket.gethostname(),
#     }
#     producer = Producer(conf)
#     return producer


# producer = create_producer()


def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed for record {}: {}".format(msg.key(), err))
        return
    print(
        "Record {} successfully produced to {} [{}] at offset {}".format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()
        )
    )


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


class MVListener(stomp.ConnectionListener):
    def __init__(self, messager, topic, producer, streaming=False):
        self.msg = messager
        self.topic = topic
        self.producer = producer
        self.streaming = streaming

    def print_message(self, message_raw):
        message = json.loads(message_raw)
        for a in message:
            body = a["body"]

            toc = a["body"].get("toc_id", "")
            platform = a["body"].get("platform", "")
            loc_stanox = "@" + body.get("loc_stanox", "")
            timestamp = int(a["body"].get("actual_timestamp", 0)) / 1000
            utc_datetime = datetime.utcfromtimestamp(timestamp)
            uk_datetime = TIMEZONE_LONDON.fromutc(utc_datetime)
            variation_status = a["body"].get("variation_status", "")

            summary = "{} ({} {}) {:<13s} {:2s} {:<6s} {:3s} {} {}".format(
                body["train_id"],
                body["train_id"][2:6],
                body["train_id"][6],
                MESSAGES[a["header"]["msg_type"]],
                toc,
                loc_stanox,
                platform,
                uk_datetime,
                variation_status,
            )
            # print(body)
            print(summary)

    def on_message(self, frame):
        """Stomp message handler"""

        headers, message_raw = frame.headers, frame.body

        # Acknowledging messages is important in client-individual mode and keep a durable subscription
        self.msg.ack(id=headers["message-id"], subscription=headers["subscription"])

        if self.streaming:
            # print(frame)
            msg = json.loads(message_raw)
            # print(msg)
            # self.producer.produce(self.topic, json.dumps(msg))
            for info in msg:
                header = info["header"]
                msg_type = header["msg_type"]
                body = info["body"]
                if msg_type == "0003":
                    # print(type(body))
                    train_records = self.producer.read_records([body])
                    self.producer.publish(
                        topic="train_movements", records=train_records
                    )
        else:
            self.print_message(message_raw)


class DataFeeder:
    """RailDataFeeder is a Python API to collect and save the real-time data from UK Network Rail Data Feed."""

    def __init__(self, topic, username, password, listener, streaming=False):
        # self.table_name = db_name.split(".")[0]
        # self.db_name = db_name
        self.topic = topic
        self.username = username
        self.password = password
        self.listener = listener
        self.streaming = streaming

    def _connect_data_feed(self):
        """
        Internal function to connect data feed using stomp connection.
        """
        conn = stomp.Connection(host_and_ports=[(HOSTNAME, 61618)])
        conn.set_listener("", self.listener(conn, self.topic, producer, self.streaming))
        conn.connect(username=self.username, passcode=self.password)

        conn.subscribe(
            **{
                "destination": f"/topic/{self.topic}",
                "id": 1,
                "ack": "client-individual",
                "activemq.subscriptionName": self.topic,
            }
        )
        return conn

    def download_feed(self):
        """
        Download the data and save the json data to local device.
        """
        conn = self._connect_data_feed()

        while True:
            try:
                sleep(10)
            except KeyboardInterrupt:
                print(
                    "Quit saving data to table and disable the connection with data feed!"
                )
                break

        conn.disconnect()


if __name__ == "__main__":
    feed_username, feed_password = secrets["openrail"].values()

    config = {
        "bootstrap.servers": "host.docker.internal:9092",
        "schema_registry.url": "http://schema-registry:8081",
        "schema.key": "/opt/resources/train_mov_key.avsc",
        "schema.value": "/opt/resources/train_mov_value.avsc",
    }
    producer = TrainAvroProducer(props=config)

    train_rdf = DataFeeder(
        topic="TRAIN_MVT_ALL_TOC",
        username=feed_username,
        password=feed_password,
        listener=MVListener,
        streaming=True,
        # streaming=False, # Use this option to preview data in the terminal
    )

    train_rdf.download_feed()
