# Setup Steps:

## Prerequisites:
- Docker Desktop (This is based on the Mac environment, the `host.docker.internal` might need to be replaced with `localhost` when using other OS)
- docker compose
- git
- terraform

# Replication 
- Clone the repository 
- Update secrets.example.toml with your own openrail API. Follow this [link](https://publicdatafeeds.networkrail.co.uk/ntrod/create-account) to create an account. Then save the file as secrets.toml
- Update dbt profiles with your own BigQuery credentials
- Terraform setup
    * Update [variable.tf](terraform_gcp/variables.tf) with your own credentials
    * Update [main.tf](terraform_gcp/main.tf) with your own credentials
    * See [README.md](terraform_gcp/README.md) for details instruction
- Run setup.sh to build the docker images
- Run `make start` to start the docker compose
- Go to orion server at `http://localhost:4200/` to create the following Blocks
    * **Need to run `prefect block register -m prefect_gcp` to make it available**
    * GCP credentials with name of **dtc-de-project-cred**
    * GCS Bucket with the name of **dtc-de-project**
    * BigQuery Warehouse with the name of **dtc-de-bq**
- Run `make stop` to stop all the dockers included in the docker compose
- 



