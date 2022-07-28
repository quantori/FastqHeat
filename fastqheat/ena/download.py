import logging
import subprocess
import typing as tp
from pathlib import Path

import backoff
import requests

from fastqheat import typing_helpers as th
from fastqheat.config import config
from fastqheat.ena.check import check_md5_checksum
from fastqheat.ena.ena_api_client import ENAClient
from fastqheat.utility import BaseEnum

logger = logging.getLogger("fastqheat.ena.download")


class TransportType(BaseEnum):
    binary = "binary"
    ftp = "ftp"


def download(
    *,
    accessions: list[str],
    output_directory: th.PathType,
    binary_path: th.PathType = "",
    attempts: int,
    attempts_interval: int,
    skip_check: bool,
    **kwargs: tp.Any,
) -> None:

    aspera_ssh_path = kwargs.get("aspera_ssh_path", "")
    transport = kwargs.get("transport", TransportType.ftp)

    download_client = ENADownloadClient(
        output_directory,
        attempts,
        attempts_interval,
        skip_check=skip_check,
        transport=transport,
        aspera_ssh_path=aspera_ssh_path,
        binary_path=binary_path,
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


class ENADownloadClient:
    def __init__(
        self,
        output_directory: th.PathType,
        attempts: int,
        attempts_interval: int,
        skip_check: bool,
        transport: TransportType,
        aspera_ssh_path: th.PathType,
        binary_path: th.PathType = "",
    ):
        self.output_directory = output_directory
        self.attempts = attempts
        self.attempts_interval = attempts_interval
        self.skip_check = skip_check
        self.binary_path = binary_path
        self.transport = transport
        self.aspera_ssh_path = aspera_ssh_path or config.PATH_TO_ASPERA_KEY
        self.transport_flag = (
            {"aspera": True} if self.transport == TransportType.binary else {"ftp": True}
        )

        if transport == TransportType.binary:
            self._download_function = backoff.on_exception(
                backoff.constant,
                subprocess.CalledProcessError,
                max_tries=attempts,
                interval=attempts_interval,
            )(self._download_via_aspera)

        else:
            self._download_function = backoff.on_exception(
                backoff.constant,
                requests.exceptions.RequestException,
                max_tries=attempts,
                interval=attempts_interval,
            )(self._download_file)

        self.download_method = (
            self.download_one_accession
            if self.skip_check
            else self.download_and_check_one_accession
        )

    def download_accession_list(self, accessions: list[str]) -> int:
        """Iterate through accession lint and download them one by one."""
        num_accessions = len(accessions)
        logger.info("There are %d accessions to download", num_accessions)
        successfully_downloaded = 0

        for accession in accessions:
            try:
                self.download_method(accession)
                successfully_downloaded += 1
            except (subprocess.CalledProcessError, requests.RequestException) as err:
                logger.info(
                    "Failed to download current run: %s. Number of attempts: %d. Error details: %s",
                    accession,
                    self.attempts,
                    err,
                )

        return successfully_downloaded

    def download_and_check_one_accession(self, accession: str) -> bool:
        logger.debug("Preparing to download an accession: %s", accession)

        links, md5s = ENAClient(
            attempts=self.attempts, attempts_interval=self.attempts_interval
        ).get_urls_and_md5s(accession, **self.transport_flag)

        accession_directory = Path(self.output_directory, accession)
        accession_directory.mkdir(parents=True, exist_ok=True)

        for url, md5 in zip(links, md5s):
            srr = url.split('/')[-1]
            file_path = accession_directory / srr
            try:
                self._download_function(url=url, file_path=file_path)
            except (subprocess.CalledProcessError, requests.RequestException) as err:
                logger.info(
                    "Failed to download current run: %s. Number of attempts: %d. Error details: %s",
                    accession,
                    self.attempts,
                    err,
                )
                return False

            if not check_md5_checksum(file_path, md5):
                logger.info("Downloaded run - %s - failed md5 check.", accession)
                return False

        logger.info("Current run - %s - has been downloaded and checked successfully", accession)
        return True

    def download_one_accession(self, accession: str) -> bool:
        logger.debug("Preparing to download an accession: %s", accession)

        links = ENAClient(
            attempts=self.attempts, attempts_interval=self.attempts_interval
        ).get_urls(accession, **self.transport_flag)

        accession_directory = Path(self.output_directory, accession)
        accession_directory.mkdir(parents=True, exist_ok=True)

        for url in links:
            srr = url.split('/')[-1]
            file_path = accession_directory / srr
            self._download_function(url=url, file_path=file_path)
            logger.info("Current Run: %s has been successfully downloaded", accession)

        return True

    def _download_via_aspera(self, url: str, file_path: th.PathType) -> None:
        logger.debug(
            "Calling aspera with parameters:\nbinary_path: %s\naspera_ssh_path: %s\nurl: %s",
            self.binary_path or 'ascp',
            self.aspera_ssh_path,
            url,
        )
        subprocess.run(
            [
                self.binary_path or 'ascp',
                '-QT',
                '-l',
                '300m',
                '-P',
                '33001',
                '-i',
                self.aspera_ssh_path,
                f'era-fasp@{url}',
                file_path,
            ],
            check=True,
        )

    def _download_file(self, url: str, file_path: th.PathType, chunk_size: int = 10**6) -> None:
        logger.debug(
            "Downloading file via ftp with parameters. url: %s\nfile_path: %s", url, file_path
        )
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size):
                    file.write(chunk)
