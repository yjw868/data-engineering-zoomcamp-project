start:
	docker build -f docker/prefect_deployment_docker -t dtc-de-project:train . \
	docker compose up -d

stop:
	docker compose down -v

update_docker_deployment:
	# docker build -f docker/prefect_deployment_docker -t dtc-de-project:train . 
	# docker run -it -d dtc-de-project:train \
	# 	/bin/sh /opt/prefect/flows/create_deployments.py
	docker exec -it prefect-agent /bin/sh flows/create_deployments.py

start_streamlit:
	docker compose --profile streamlit up -d 