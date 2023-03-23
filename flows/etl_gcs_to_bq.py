import json
from io import BytesIO

import pandas as pd
from prefect import flow, task
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket


@task(retries=0, log_prints=True)
def extrct_from_gcs():
    gcs_block = GcsBucket.load("dtc-de-project")
    with BytesIO() as buf:
        gcs_block.download_object_to_file_object(
            "train_mov/20230322-001500-29.json", buf
        )
        buf.seek(0)

        df = pd.DataFrame.from_dict(json.loads(str(buf.read(), "utf-8")))
        return df


@task()
def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to BiqQuery"""

    gcp_credentials_block = GcpCredentials.load("dtc-de-project-cred")

    df.to_gbq(
        destination_table="trains.movements",
        project_id="dtc-de-project-380810",
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        chunksize=500_000,
        if_exists="append",
    )


@flow()
def etl_gcs_to_bq():
    df = extrct_from_gcs()
    write_bq(df)


if __name__ == "__main__":
    etl_gcs_to_bq()
