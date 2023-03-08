import json
import socket
from datetime import datetime
from time import sleep

import stomp
import toml
from confluent_kafka import Producer
from pytz import timezone

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


topic = "public.networkrail.movement"
conf = {
    "bootstrap.servers": "host.docker.internal:9092",
    "client.id": socket.gethostname(),
}
producer = Producer(conf)


class MVListener(stomp.ConnectionListener):
    def __init__(self, messager, topic, sender, streaming=False):
        self.msg = messager
        self.topic = topic
        self.sender = sender
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
            print(message_raw)
            self.sender.produce(self.topic, message_raw)
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
                sleep(1)
            except KeyboardInterrupt:
                print(
                    "Quit saving data to table and disable the connection with data feed!"
                )
                break

        conn.disconnect()


if __name__ == "__main__":
    feed_username, feed_password = secrets["openrail"].values()

    train_rdf = DataFeeder(
        topic="TRAIN_MVT_ALL_TOC",
        username=feed_username,
        password=feed_password,
        listener=MVListener,
        streaming=True,
    )

    train_rdf.download_feed()
