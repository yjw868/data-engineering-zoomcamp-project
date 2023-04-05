import pickle
from pathlib import Path
from time import sleep

import prefect

# from dotenv import load_dotenv
from prefect import flow, get_run_logger, task
from prefect.blocks.system import String
from prefect.filesystems import LocalFileSystem
from prefect_gcp.cloud_storage import GcsBucket
from pytz import timezone

# data map to /opt/prefect in docker container
loc = Path(__file__).parents[1] / "data"


@task()
def write_gcs(path: Path) -> None:
    """Upload local parquet file to GCS"""
    to_path = Path("train_mov") / path.name
    gcs_block = GcsBucket.load("dtc-de-project")
    # gcs_block = GcsBucket.load("dtc-project-gcs")
    gcs_block.upload_from_path(from_path=path, to_path=to_path)
    return


@flow()
def etl_local_to_gcs():
    p = Path(loc).glob("*.json")
    files = [x for x in p if x.is_file()]
    with open("./data/processed_files.pkl", "rb") as f:
        try:
            processed_files = pickle.load(f)
            delta = set(files).symmetric_difference(set(processed_files))
            files_to_write = list(delta)
        except EOFError:
            files_to_write = files

    if len(files_to_write) == 0:
        print("No new files to process")
    else:
        for file in files_to_write:
            path = Path(f"{file}")
            write_gcs(path)
        with open("./data/processed_files.pkl", "wb") as f:
            pickle.dump(files, f)


if __name__ == "__main__":
    etl_local_to_gcs()
