import logging
import subprocess
from abc import abstractmethod
from pathlib import Path

import requests

from fastqheat.backend.ena.ena_api_client import ENAClient
from fastqheat.backend.failed_output_writer import FailedAccessionWriter
from fastqheat.exceptions import ValidationError

logger = logging.getLogger("fastqheat.backend.common")


class BaseAccessionChecker:
    def __init__(self, directory: Path, attempts: int, attempts_interval: int) -> None:
        self.directory = directory
        self.attempts = attempts
        self.attempts_interval = attempts_interval
        self.failed_accession_writer = FailedAccessionWriter(self.directory)
        self.ena_client = ENAClient(attempts, attempts_interval)

    def check_accessions(self, accessions: list[str]) -> int:
        num_accessions = len(accessions)
        logger.info("There are %d accessions to check", num_accessions)
        successfully_checked = 0

        for accession in accessions:
            try:
                self.check_accession(accession)
                successfully_checked += 1
            except (ValidationError, FileNotFoundError, requests.RequestException) as err:
                logger.error(err)
                self.failed_accession_writer.add_accession(accession)

        return successfully_checked

    @abstractmethod
    def check_accession(self, accession: str) -> bool:
        pass


class BaseDownloadClient:
    def __init__(
        self, output_directory: Path, attempts: int, attempts_interval: int, skip_check: bool
    ):
        self.output_directory = Path(output_directory)
        self.attempts = attempts
        self.attempts_interval = attempts_interval
        self.skip_check = skip_check
        self.failed_output_writer = FailedAccessionWriter(self.output_directory)

    def download_accession_list(self, accessions: list[str]) -> int:
        """Iterate through accession lint and download them one by one."""
        num_accessions = len(accessions)
        logger.info("There are %d accessions to download", num_accessions)
        successfully_downloaded = 0

        for accession in accessions:
            try:
                self.download_one_accession(accession)
                successfully_downloaded += 1
            except (
                subprocess.CalledProcessError,
                requests.RequestException,
                ValidationError,
            ) as err:
                logger.info(
                    "Failed to download current run: %s. Number of attempts: %d. Error details: %s",
                    accession,
                    self.attempts,
                    str(err),
                )
                self.failed_output_writer.add_accession(accession)

        return successfully_downloaded

    @abstractmethod
    def download_one_accession(self, accession: str) -> None:
        pass
