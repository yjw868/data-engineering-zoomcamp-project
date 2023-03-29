import json
from datetime import datetime

import stomp
from pytz import timezone

TIMEZONE_LONDON: timezone = timezone("Europe/London")

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


class MQListener(stomp.ConnectionListener):
    def __init__(self, messager, mv_subscribe_topic, topic, producer, streaming=False):
        self.msg = messager
        self.producer_topic = topic
        self.topic = mv_subscribe_topic
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
                        topic=self.producer_topic, records=train_records
                    )
        else:
            self.print_message(message_raw)
