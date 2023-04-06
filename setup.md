# Setup Steps:

## Prerequisites:
- Docker Desktop (This is based on the Mac environment, the `host.docker.internal` might need to be replaced with `localhost` when using other OS)
- docker compose
- git
- terraform

## Replication 
- Clone the repository 
- Update [secrets.example.toml](secrets.example.toml) with your own openrail API. Follow this [link](https://publicdatafeeds.networkrail.co.uk/ntrod/create-account) to create an account. Then save the file as secrets.toml.
[Optinal] If you want connect the streamlit to query BigQuery, please add your google service account credential to the [gcp_service_account]
- Update dbt [profiles](profile-yml/profiles.yml) with your own BigQuery credentials.
- Update [docker-compose.yml](docker-compose.yml#L260) line 260 with your google service account credential location
- Terraform setup
    * Update [variable.tf](terraform_gcp/variables.tf) with your own credentials
    * Update [main.tf](terraform_gcp/main.tf) with your own credentials
    * See [README.md](terraform_gcp/README.md) for details instruction
- Run setup.sh to build the docker images
- Run `make start` to start the docker compose
- Go to orion server at `http://localhost:4200/` to create the following Blocks

    *** **Need to run `prefect block register -m prefect_gcp` to make it available** ***
    * GCP credentials with name of **dtc-de-project-cred**
    * GCS Bucket with the name of **dtc-de-project**
    * BigQuery Warehouse with the name of **dtc-de-bq**
-  The etl_kafka_to_gcs.avro deployment is a streaming operation. Unfortunately, I could not figure out how to programatically termimate it gracely. Due to this, I haven't scheduled it. Please use quick run in the Prefect UI to trigger it. 
<img src="assets/trigger prefect deployment.png" />
- Run `make stop` to stop all the dockers included in the docker compose

### Troubleshooting

- I run into the issue serctes.toml is converted to a directory within the streamlit docker. I couldn't figure out the exactly cause so I have to mannuly create this file after the docker is created.
Run `docker exec -it streamlit /bin/sh` to log into the docker console
Create the secrets.toml file

