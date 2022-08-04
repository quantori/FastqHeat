import asyncio
import logging
import typing as tp
from pathlib import Path

import aiocsv
import aiofiles
import aiohttp

from fastqheat.backend.ena.ena_api_client import ENAAsyncClient
from fastqheat.config import config

logger = logging.getLogger("fastqheat.ena.metadata")

T = tp.TypeVar("T")

BATCH_SIZE = 5  # how many requests we make simultaneously to ENA API. Actually, I don't know
# what is the limit, but to be on the safe side I have chosen 5

WRITING_COROUTINE_SLEEP_TIMEOUT = 1


async def download_metadata(
    *,
    directory: str,
    accession: list[str],
    attempts: int = config.MAX_ATTEMPTS,
    attempts_interval: int = 0,
    **kwargs: tp.Any,
) -> None:

    metadata_downloader = MetadataDownloader(Path(directory), attempts, attempts_interval)
    successful_num = await metadata_downloader.download(accession)

    logger.info(
        "%d/%d metadata rows were successfully written to %s",
        successful_num,
        len(accession),
        directory,
    )


class MetadataDownloader:
    """
    Class for downloading and saving metadata from ENA API to a given *.csv file.
    Usage example:

    metadata_downloader = MetadataDownloader(Path(directory), attempts, attempts_interval)

    successful_num = await metadata_downloader.download(['SRR7969880', 'SRR7969881'])

    logger.info(
        "%d/%d metadata rows were successfully written to %s",
        successful_num,
        len(accession),
        directory,
    )

    The only public method is a coroutine download_metadata(). It downloads and writes metadata
    asynchronously using two coroutines (one gets the data from the ENA API, the other - writes
    this data to the csv file), which work independently and communicating via a queue.
    """

    def __init__(
        self,
        directory: Path,
        attempts: int,
        attempts_interval: int,
        batch_size: int = BATCH_SIZE,
        writing_coroutine_sleep_timeout: int = WRITING_COROUTINE_SLEEP_TIMEOUT,
    ):
        self.directory: Path = directory

        # how many requests we make simultaneously to ENA API
        self._batch_size: int = batch_size
        # how much coroutine that writes to a csv sleep between checkin the queue of data
        self._writing_coroutine_sleep_timeout: int = writing_coroutine_sleep_timeout
        self._ena_async_client: ENAAsyncClient = ENAAsyncClient(
            attempts=attempts, attempts_interval=attempts_interval
        )
        self._ena_fields: list[str] = []
        self._queue: asyncio.Queue = asyncio.Queue()

    async def download(self, accessions: list[str]) -> int:
        """Orchestrates the process of downloading and saving the metadata."""
        async with aiohttp.ClientSession() as session:
            self._ena_async_client.session = session
            self._ena_fields = await self._ena_async_client.get_ena_fields()

            stop = asyncio.Event()
            _, successful_num = await asyncio.gather(
                self._get_data_in_batches(accessions, stop), self._write_data(stop)
            )
        return successful_num

    async def _get_data_in_batches(self, accessions: list[str], stop: asyncio.Event) -> None:
        """Get metadata from ENA API in batches of simultaneous async requests."""
        for batch_accessions in (
            accessions[i : i + self._batch_size]
            for i in range(0, len(accessions), self._batch_size)
        ):
            await asyncio.gather(*[self._get_data(accession) for accession in batch_accessions])

        logger.debug("Ran out of accessions...")
        stop.set()  # communicates to the _write_data coroutine to stop waiting on the queue

    async def _get_data(self, accession: str) -> None:
        """Get metadata from ENA and put it to the queue."""
        logger.debug("Getting metadata for %s", accession)
        fields_str = ",".join([field for field in self._ena_fields])
        data = await self._ena_async_client.get_metadata(accession, fields_str)
        await self._queue.put(data[0])

    async def _write_data(self, stop: asyncio.Event) -> int:
        """Listen to the queue and write data to the csv file if there is something in the queue."""
        successful = 0
        async with aiofiles.open(self.directory, 'w', encoding="utf-8", newline="") as csvfile:
            writer = aiocsv.AsyncDictWriter(csvfile, self._ena_fields)
            await writer.writeheader()

            # write to file until we get an event to stop and the queue is empty
            while not (stop.is_set() and self._queue.empty()):
                if self._queue.empty():
                    logger.debug(
                        "Queue is empty. Going to sleep %d seconds...",
                        self._writing_coroutine_sleep_timeout,
                    )
                    await asyncio.sleep(self._writing_coroutine_sleep_timeout)
                    continue

                data = await self._queue.get()
                logger.debug("Writing %s to the csv file...", data.get("run_accession"))
                await writer.writerow(data)
                successful += 1
            logger.debug("Closing file...")
        return successful
