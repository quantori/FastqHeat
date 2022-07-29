import datetime as dt
from pathlib import Path


class FailedAccessionWriter:
    def __init__(self, path_to_dir: Path):

        if not path_to_dir.is_dir():
            raise FileNotFoundError(f"Path does not exists or is not a directory: {path_to_dir}")
        self.path_to_dir = path_to_dir

        now = dt.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")  # e.g. '2022_07_28_17_58_17'

        self.path_to_file = self.path_to_dir / f"failed_list_{now}.txt"

    def add_accession(self, accession: str) -> None:
        if not self.path_to_file.exists():
            self.path_to_file.touch()

        with open(self.path_to_file, "a") as file:
            file.write(f"{accession}\n")
