from prefect.infrastructure.docker import DockerContainer

docker_block = DockerContainer(
    image="dtc-de-project:train",
    auto_remove=True,
    networks=["dtc-network"],
)

docker_block.save("train", overwrite=True)
