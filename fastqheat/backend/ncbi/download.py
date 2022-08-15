import logging
import subprocess
import typing as tp
from pathlib import Path

import backoff

from fastqheat.backend.common import BaseDownloadClient
from fastqheat.backend.failed_output_writer import FailedAccessionWriter
from fastqheat.backend.ncbi.check import AccessionChecker
from fastqheat.config import config
from fastqheat.exceptions import ValidationError

logger = logging.getLogger("fastqheat.ncbi.download")


def download(
    *,
    output_directory: Path,
    accessions: list[str],
    attempts: int = config.DEFAULT_MAX_ATTEMPTS,
    attempts_interval: int,
    core_count: int,
    skip_check: bool,
    **kwargs: tp.Any,
) -> None:

    download_client = NCBIDownloadClient(
        output_directory,
        attempts,
        attempts_interval,
        skip_check,
        core_count=core_count,  # todo: get default from config
    )

    successfully_downloaded = download_client.download_accession_list(accessions)
    num_accessions = len(accessions)

    if skip_check:
        logger.info(
            "%d/%d runs were downloaded successfully.", successfully_downloaded, num_accessions
        )
    else:
        logger.info(
            "%d/%d runs were downloaded and checked successfully.",
            successfully_downloaded,
            num_accessions,
        )


class NCBIDownloadClient(BaseDownloadClient):
    def __init__(
        self,
        output_directory: Path,
        attempts: int,
        attempts_interval: int,
        skip_check: bool,
        core_count: int,
    ):
        self.output_directory = Path(output_directory)
        self.failed_output_writer = FailedAccessionWriter(self.output_directory)
        self.attempts = attempts

        super().__init__(output_directory, attempts, attempts_interval, skip_check)

        self.core_count = core_count
        self._download_function = backoff.on_exception(
            backoff.constant,
            subprocess.CalledProcessError,
            jitter=None,  # The jitter is disabled in order to keep attempts interval fixed
            max_tries=attempts,
            interval=attempts_interval,
        )(self._download_via_fastrq_dump)

        self.accession_checker = AccessionChecker(
            directory=Path(output_directory),
            attempts=attempts,
            attempts_interval=attempts_interval,
            core_count=core_count,
            zipped=False,
        )

    def download_one_accession(self, accession: str) -> None:
        """
        Download the run from NCBI's Sequence Read Archive (SRA)
        Uses fasterq_dump and check completeness of downloaded fastq file
        """

        accession_directory = Path(self.output_directory, accession)
        accession_directory.mkdir(parents=True, exist_ok=True)

        logger.info('Trying to download %s file', accession)

        self._download_function(accession=accession, accession_directory=accession_directory)

        if self.skip_check:
            self._zip(accession_directory, accession)
            return

        if not self.accession_checker.check_accession(accession=accession):
            raise ValidationError("Downloaded run - %s - is not valid.", accession)

        self._zip(accession_directory, accession)

    def _zip(self, accession_directory: Path, accession: str) -> None:
        fastq_files = list(accession_directory.glob(f'{accession}*.fastq'))
        logger.info("Compressing FASTQ files for %s in %s", accession, accession_directory)
        subprocess.run(['pigz', '--processes', str(self.core_count), *fastq_files], check=True)
        logger.info("FASTQ files for %s have been zipped", accession)

    def _download_via_fastrq_dump(self, accession: str, accession_directory: Path) -> None:
        logger.debug("Downloading accession %s using fasterq-dump...", accession)
        subprocess.run(
            [
                'fasterq-dump',
                accession,
                '-O',
                accession_directory,
                '-p',
                '--threads',
                str(self.core_count),
            ],
            check=True,
        )
