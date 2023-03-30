from etl_gcs_to_bq_batch import etl_gcs_to_bq
from etl_kafka_to_local_avro import etl_kafka_to_local
from etl_local_to_gcs_batch import etl_local_to_gcs
from prefect.deployments import Deployment
from prefect.infrastructure.docker import DockerContainer

docker_block = DockerContainer.load("train")
etl_gcs_to_bq_deployment = Deployment.build_from_flow(
    flow=etl_gcs_to_bq,
    name="etl_gcs_to_bq",
    entrypoint="flows/etl_gcs_to_bq_batch.py:etl_gcs_to_bq",
)

etl_kafka_to_local_docker_deployment = Deployment.build_from_flow(
    flow=etl_kafka_to_local,
    name="etl_kafka_to_local_docker",
    infrastructure=docker_block
    # entrypoint="flows/etl_kafka_to_local_avro.py:etl_kafka_to_local",
)

etl_kafka_to_local_deployment = Deployment.build_from_flow(
    flow=etl_kafka_to_local,
    name="etl_kafka_to_local",
    entrypoint="flows/etl_kafka_to_local_avro.py:etl_kafka_to_local",
)

etl_local_to_gcs_deployment = Deployment.build_from_flow(
    flow=etl_local_to_gcs,
    name="etl_local_to_gcs",
    entrypoint="flows/etl_local_to_gcs_batch.py:etl_local_to_gcs",
)

if __name__ == "__main__":
    etl_gcs_to_bq_deployment.apply()
    etl_kafka_to_local_docker_deployment.apply()
    etl_kafka_to_local_deployment.apply()
