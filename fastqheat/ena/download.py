import logging
import subprocess
from pathlib import Path

import backoff
import requests

from fastqheat import typing_helpers as th
from fastqheat.config import config
from fastqheat.ena.check import md5_checksum
from fastqheat.ena.ena_api_client import ENAClient
from fastqheat.utility import BaseEnum

logger = logging.getLogger("fastqheat.ena.download")


class TransportType(BaseEnum):
    aspera = "aspera"
    ftp = "ftp"


def download(
    *,
    accessions: list[str],
    output_directory: th.PathType,
    binary_path: th.PathType = "",
    attempts: int,
    attempts_interval: int,
    **kwargs,
) -> bool:

    aspera_ssh_path = kwargs.get("aspera_ssh_path", "")
    transport = kwargs.get("transport", TransportType.ftp)

    download_client = ENADownloadClient(
        output_directory,
        attempts,
        attempts_interval,
        transport=transport,
        aspera_ssh_path=aspera_ssh_path,
        binary_path=binary_path,
    )

    return download_client.download_accession_list(accessions)


class ENADownloadClient:
    def __init__(
        self,
        output_directory: th.PathType,
        attempts: int,
        attempts_interval: int,
        transport: TransportType,
        aspera_ssh_path: th.PathType,
        binary_path: th.PathType = "",
    ):
        self.output_directory = output_directory
        self.attempts = attempts
        self.attempts_interval = attempts_interval
        self.binary_path = binary_path
        self.transport = transport
        self.aspera_ssh_path = aspera_ssh_path or config.PATH_TO_ASPERA_KEY

        if transport == TransportType.aspera:
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

    def download_accession_list(self, accessions: list[str]) -> bool:
        logger.info("There are %d accessions to download", len(accessions))
        return all(self.download_one_accession(accession) for accession in accessions)

    def download_one_accession(self, accession: str) -> bool:
        logger.debug("Preparing to download an accession: %s", accession)
        transport_flag = (
            {"aspera": True} if self.transport == TransportType.aspera else {"ftp": True}
        )

        links, md5s = ENAClient(
            attempts=self.attempts, attempts_interval=self.attempts_interval
        ).get_urls_and_md5s(accession, **transport_flag)

        accession_directory = Path(self.output_directory, accession)
        accession_directory.mkdir(parents=True, exist_ok=True)

        successful = True
        for url, md5 in zip(links, md5s):
            srr = url.split('/')[-1]
            file_path = accession_directory / srr
            self._download_function(url=url, file_path=file_path)

            if not md5_checksum(file_path, md5):
                successful = False

        if successful:
            logger.info("Current Run: %s has been successfully downloaded", accession)

        return successful

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
