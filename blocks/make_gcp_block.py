from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket

# Registering blocks
# Register blocks in this module to view and edit them on Prefect Cloud:
# ```prefect block register -m prefect_gcp````

# This can be done under Prefect Orion UI
# Copy your own service_account_info dictionary from the json file you downloaded from google
# IMPORTANT - do not store credentials in a publicly available repository!


credentials_block = GcpCredentials(
    # Enter your credentials from the json file
    service_account_info={
        "type": "********",
        "project_id": "********",
        "private_key_id": "********",
        "private_key": "********",
        "client_email": "********",
        "client_id": "********",
        "auth_uri": "********",
        "token_uri": "********",
        "auth_provider_x509_cert_url": "********",
        "client_x509_cert_url": "********",
    }
)
credentials_block.save("dtc-de-project-cred", overwrite=True)


bucket_block = GcsBucket(
    gcp_credentials=GcpCredentials.load("dtc-de-project-cred"),
    bucket="dtc_data_lake_dtc-de-project-380810",  # insert your  GCS bucket name
)

bucket_block.save("dtc-de-project", overwrite=True)
