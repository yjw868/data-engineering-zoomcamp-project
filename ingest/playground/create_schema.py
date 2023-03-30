from schema_registry.client import SchemaRegistryClient, schema

# from confluent_kafka.schema_registry import SchemaRegistryClient, schema

client = SchemaRegistryClient(url="http://host.docker.internal:8081")
# client.update_compatibility(level="NONE", subject="TRAIN_MVT_ALL_TOC")
print(client.get_subjects())
my_schema = client.get_schema(subject="TRAIN_MVT_ALL_TOC", version="latest")
# print(my_schema)

deployment_schema = {
    "type": "record",
    "namespace": "dtc-project",
    "name": "value_TRAIN_MVT_ALL_TOC",
    "fields": [
        {"name": "event_type", "type": "string"},
        {"name": "gbtt_timestamp", "type": "string"},
        {"name": "original_loc_stanox", "type": "string"},
        {"name": "planned_timestamp", "type": "string"},
        {"name": "timetable_variation", "type": "string"},
        {"name": "original_loc_timestamp", "type": "string"},
        {"name": "current_train_id", "type": "null"},
        {"name": "delay_monitoring_point", "type": "string"},
        {"name": "next_report_run_time", "type": "string"},
        {"name": "reporting_stanox", "type": "string"},
        {"name": "actual_timestamp", "type": "string"},
        {"name": "correction_ind", "type": "string"},
        {"name": "event_source", "type": "string"},
        {"name": "train_file_address", "type": "string"},
        {"name": "platform", "type": "string"},
        {"name": "division_code", "type": "string"},
        {"name": "train_terminated", "type": "string"},
        {"name": "train_id", "type": "string"},
        {"name": "offroute_ind", "type": "string"},
        {"name": "variation_status", "type": "string"},
        {"name": "train_service_code", "type": "string"},
        {"name": "toc_id", "type": "string"},
        {"name": "loc_stanox", "type": "string"},
        {"name": "auto_expected", "type": "string"},
        {"name": "direction_ind", "type": "string"},
        {"name": "route", "type": "string"},
        {"name": "planned_event_type", "type": "string"},
        {"name": "next_report_stanox", "type": "string"},
        {"name": "line_ind", "type": "string"},
    ],
}

avro_schema = schema.AvroSchema(deployment_schema)
schema_id = client.register("value_TRAIN_MVT_ALL_TOC", avro_schema)
print(schema_id)
print(client.get_by_id(1))
