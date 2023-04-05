from etl_gcs_to_bq_batch import etl_gcs_to_bq
from etl_kafka_to_gcs_avro import etl_kafka_to_gcs
from prefect.deployments import Deployment
from prefect.infrastructure.docker import DockerContainer
from prefect.server.schemas.schedules import CronSchedule

docker_block = DockerContainer.load("train")
etl_gcs_to_bq_deployment = Deployment.build_from_flow(
    flow=etl_gcs_to_bq,
    name="etl_gcs_to_bq",
    entrypoint="flows/etl_gcs_to_bq_batch.py:etl_gcs_to_bq",
    schedule=(CronSchedule(cron="*/10 * * * *", timezone="Europe/London")),
)

etl_kafka_to_gcs_docker_deployment = Deployment.build_from_flow(
    flow=etl_kafka_to_gcs, name="etl_kafka_to_gcs_docker", infrastructure=docker_block
)

if __name__ == "__main__":
    etl_gcs_to_bq_deployment.apply()
    etl_kafka_to_gcs_docker_deployment.apply()
