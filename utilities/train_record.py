from typing import Dict, List


class TrainRecord:
    def __init__(self, arr: List[str]):
        print(arr)
        self.event_type = str(arr[0])
        self.gbtt_timestamp = int(arr[1] or 0)
        self.original_loc_stanox = int(arr[2] or 0)
        self.planned_timestamp = int(arr[3] or 0)
        self.timetable_variation = int(arr[4])
        self.original_loc_timestamp = int(arr[5] or 0)
        self.current_train_id = str(arr[6])
        self.delay_monitoring_point = str(arr[7])
        self.next_report_run_time = int(arr[8] or 0)
        self.reporting_stanox = int(arr[9])
        self.actual_timestamp = int(arr[10])
        self.correction_ind = str(arr[11])
        self.event_source = str(arr[12])
        self.train_file_address = str(arr[13])
        self.platform = str(arr[14])
        self.division_code = int(arr[15])
        self.train_terminated = str(arr[16])
        self.train_id = str(arr[17])
        self.offroute_ind = str(arr[18])
        self.variation_status = str(arr[19])
        self.train_service_code = int(arr[20])
        self.toc_id = int(arr[21])
        self.loc_stanox = int(arr[22])
        self.auto_expected = str(arr[23])
        self.direction_ind = str(arr[24])
        self.route = str(arr[25])
        self.planned_event_type = str(arr[26])
        self.next_report_stanox = int(arr[27] or 0)
        self.line_ind = str(arr[28])

    @classmethod
    def from_dict(cls, d: Dict):
        # print(d)
        return cls(
            arr=[
                d["event_type"],
                d["gbtt_timestamp"],
                d["original_loc_stanox"],
                d["planned_timestamp"],
                d["timetable_variation"],
                d["original_loc_timestamp"],
                d["current_train_id"],
                d["delay_monitoring_point"],
                d["next_report_run_time"],
                d["reporting_stanox"],
                d["actual_timestamp"],
                d["correction_ind"],
                d["event_source"],
                d["train_file_address"],
                d["platform"],
                d["division_code"],
                d["train_terminated"],
                d["train_id"],
                d["offroute_ind"],
                d["variation_status"],
                d["train_service_code"],
                d["toc_id"],
                d["loc_stanox"],
                d["auto_expected"],
                d["direction_ind"],
                d["route"],
                d["planned_event_type"],
                d["next_report_stanox"],
                d["line_ind"],
            ]
        )

    def __repr__(self):
        return f"{self.__class__.__name__}: {self.__dict__}"


def dict_to_train_record(obj, ctx):
    if obj is None:
        return None

    return TrainRecord.from_dict(obj)


def train_record_to_dict(train_record: TrainRecord, ctx=None):
    return train_record.__dict__
