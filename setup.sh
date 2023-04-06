#!/bin/bash

if [ ! -f "secrect.toml" ]; then
    echo "Create secrect.toml. Remember to update it with your detail. \n
        Go to https://publicdatafeeds.networkrail.co.uk/ntrod/create-account to create your own account"
    touch secrets.toml
fi

# create a network for Prefect DockerContainer deployment
if [ ! "$(docker network ls | grep dtc-network)" ]; then
    echo "\n**Create docker network"
    docker network create -d bridge dtc-network
else
    echo "dtc-network already exists."
fi

# Use this to spine up all contains to keep the bash simple
# Wait for all image to build
echo  "\n**Start all containers"
echo  "\n**Please wait for 2 minutes for ensure all images are built"
docker compose up -d


# sleep 60

echo  "\n**Init dbt project"
docker exec  dbt-bq-train  /bin/sh -c 'dbt deps; dbt run'
# read

echo "------"
echo "DONE"
echo ""
echo "Now head over to http://localhost:4200 to view Prefect flows"