from prefect.infrastructure.docker import DockerContainer

docker_block = DockerContainer(
    image="dtc-de-project:train",
    auto_remove=True,
    networks=["dtc-network"],
    # volumes=["data/prefect_data:/opt/prefect/data"],
)

docker_block.save("train", overwrite=True)
