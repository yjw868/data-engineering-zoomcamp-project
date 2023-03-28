from time import sleep

import stomp
import toml
from MQListenner import MQListener
from train_avro_producer import TrainAvroProducer

with open("../secrets.toml", "r") as f:
    secrets = toml.load(f)

# Message type
# Datafeeds for information on the Open Data available from the rail industry in Great Britain
HOSTNAME = "datafeeds.networkrail.co.uk"


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
        listener=MQListener,
        streaming=True,
        # streaming=False, # Use this option to preview data in the terminal
    )

    train_rdf.download_feed()
