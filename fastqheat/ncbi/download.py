import logging
import subprocess
from functools import partial
from pathlib import Path

import backoff

import fastqheat.typing_helpers as th
from fastqheat.config import config
from fastqheat.ncbi.check import check_accession

logger = logging.getLogger("fastqheat.ncbi.download")


def download(
    *,
    output_directory: th.PathType,
    accessions: list[str],
    attempts: int = config.MAX_ATTEMPTS,
    attempts_timeout: int,
    **kwargs,
) -> bool:

    download_client = NCBIDownloadClient(
        output_directory,
        attempts,
        attempts_timeout,
        core_count=kwargs.get("core_count", 6),  # todo: get from config
    )

    return download_client.download_accession_list(accessions)


class NCBIDownloadClient:
    def __init__(
        self,
        output_directory: th.PathType,
        attempts: int,
        attempts_interval: int,
        core_count: int,
    ):
        self.output_directory = output_directory
        self.core_count = core_count
        self.download_function = backoff.on_exception(
            backoff.constant,
            subprocess.CalledProcessError,
            max_tries=attempts,
            interval=attempts_interval,
        )(self._download_via_fastrq_dump)

        self.check_func = partial(
            check_accession,
            attempts=attempts,
            attempts_interval=attempts_interval,
            internal_check=True,
        )

    def download_accession_list(self, accessions: list[str]) -> bool:
        return all(self.download_one_accession(accession) for accession in accessions)

    def download_one_accession(self, accession) -> bool:
        """

        Download the run from NCBI's Sequence Read Archive (SRA)
        Uses fasterq_dump and check completeness of downloaded fastq file
        Parameters
        ----------
        accession: str
            a string of Study Accession
        Returns
        -------
        bool
            True if run was correctly downloaded, otherwise - False
        """
        accession_directory = Path(self.output_directory, accession)
        accession_directory.mkdir(parents=True, exist_ok=True)

        logger.info('Trying to download %s file', accession)

        self.download_function(accession=accession, accession_directory=accession_directory)
        # check completeness of the file and return boolean
        correctness = self.check_func(accession=accession, path=accession_directory)

        if correctness:
            fastq_files = list(accession_directory.glob(f'{accession}*.fastq'))
            logger.info("Compressing FASTQ files for %s in %s", accession, accession_directory)
            subprocess.run(['pigz', '--processes', str(self.core_count), *fastq_files], check=True)
            logger.info("FASTQ files for %s have been zipped", accession)

        return correctness

    def _download_via_fastrq_dump(self, accession: str, accession_directory: str) -> None:
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
