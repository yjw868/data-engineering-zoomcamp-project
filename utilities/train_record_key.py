from typing import Dict, TypedDict


class TrainRecordKey:
    def __init__(self, train_id):
        self.train_id = train_id

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(train_id=d["train_id"])

    def __repr__(self):
        return f"{self.__class__.__name__}: {self.__dict__}"


def dict_to_train_record_key(obj, ctx):
    if obj is None:
        return None

    return TrainRecordKey.from_dict(obj)


def train_record_key_to_dict(train_record_key: TrainRecordKey, ctx):
    return train_record_key.__dict__
