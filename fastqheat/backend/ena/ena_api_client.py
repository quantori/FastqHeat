import logging
import typing as tp

import aiohttp
import backoff
import requests
from requests import RequestException

from fastqheat import typing_helpers as th
from fastqheat.config import config
from fastqheat.exceptions import ENAClientError

logger = logging.getLogger("fastqheat.ena.ena_api_client")


class BaseENAClient:
    """
    Client to work with European Nucleotide Archive public API.

    Swagger: https://www.ebi.ac.uk/ena/portal/api/
    """

    def __init__(self) -> None:
        self._base_url: str = "https://www.ebi.ac.uk/ena/portal/api/"
        self._filereport_url: str = f"{self._base_url}{'filereport'}"
        self._query_params: dict[str, str] = {"result": "read_run", "format": "json"}


class ENAAsyncClient(BaseENAClient):
    def __init__(
        self,
        attempts: int = config.DEFAULT_MAX_ATTEMPTS,
        attempts_interval: int = 1,
        session: tp.Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Async client for working with ENA API."""

        super().__init__()

        self._return_fields_url: str = f"{self._base_url}{'returnFields'}"
        self._all_ena_fields: list[str] = []
        self._session: tp.Optional[aiohttp.ClientSession] = session

        self._get_json = backoff.on_exception(
            backoff.constant,
            exception=aiohttp.ClientResponseError,
            jitter=None,  # The jitter is disabled in order to keep attempts interval fixed
            max_tries=attempts,
            interval=attempts_interval,
        )(self._base_get_json)

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("aiohttp.ClientSession is not set.")
        return self._session

    @session.setter
    def session(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_ena_fields(self) -> list[str]:
        if not self._all_ena_fields:
            self._all_ena_fields = await self._get_all_ena_fields()
        return self._all_ena_fields

    async def _get_all_ena_fields(self) -> list[str]:
        params = {"dataPortal": "ena", **self._query_params}
        try:
            response = await self._get_json(params=params, url=self._return_fields_url)
        except aiohttp.ClientResponseError as err:
            logger.exception(err)
            logger.error("Error occurred during getting fields for metadata from ENA API.")
            raise ENAClientError

        '''
        Response looks like this:

        [
          {
            "columnId": "study_accession",
            "description": "study accession number"
          },
          {
            "columnId": "secondary_study_accession",
            "description": "secondary study accession number"
          },
        ...
        ]
        '''

        return [field["columnId"] for field in response]

    async def get_metadata(self, accession: str, fields: str) -> list[th.JsonDict]:
        """
        Get data for an accession with all available fields in json format.

        Example of returned data:
        [{'accession': 'SAMN10181503',
          'altitude': '',
          'assembly_quality': '',
          'assembly_software': '',
          'base_count': '22674621',
          'binning_software': '',
          'bio_material': 'soil',
          'broker_name': '',
          ...
          }
        ]
        """

        params = {**self._query_params, "fields": fields, "accession": accession}
        response_data = await self._get_data(
            term=accession,
            params=params,
            error_message="An error occurred while getting metadata",
            url=self._filereport_url,
        )
        return response_data

    async def _get_data(
        self, term: str, params: dict[str, str], error_message: str, url: str = ""
    ) -> list[th.JsonDict]:
        try:
            response_data = await self._get_json(url=url, params=params)
        except aiohttp.ClientResponseError as err:
            logger.exception(err)
            logger.error("%s. Accession: %s", error_message, term)
            raise ENAClientError

        if not response_data:
            logger.error("ENA API returned no data for the accession: %s. Cannot proceed", term)
            raise ENAClientError

        return response_data

    async def _base_get_json(self, params: dict[str, str], url: str = '') -> list[th.JsonDict]:
        """Base get json method."""
        response = await self._session.get(url or self._base_url, params=params)  # type: ignore
        response.raise_for_status()
        if response.status == 204:  # ENA API returns 204 instead of 404
            return []
        return await response.json()


class ENAClient(BaseENAClient):
    """
    Client to work with European Nucleotide Archive public API.

    Swagger: https://www.ebi.ac.uk/ena/portal/api/
    """

    def __init__(
        self, attempts: int = config.DEFAULT_MAX_ATTEMPTS, attempts_interval: int = 1
    ) -> None:
        super().__init__()

        self._get_json = backoff.on_exception(
            backoff.constant,
            exception=RequestException,
            jitter=None,  # The jitter is disabled in order to keep attempts interval fixed
            max_tries=attempts,
            interval=attempts_interval,
        )(self._base_get_json)

    def get_srr_ids_from_srp(self, term: str) -> list[str]:
        """Returns list of SRR(ERR) IDs based on the given SRP(ERP) ID."""

        srr_ids = []

        params = {**self._query_params, "accession": term}
        response_data = self._get_data(
            term=term,
            params=params,
            error_message="An error occurred getting list of SRR for the given SRP from ENA API",
        )

        for data in response_data:
            srr_ids.append(data['run_accession'])
        return srr_ids

    def get_md5s(self, term: str) -> list[str]:
        """Returns hashes based on given term."""

        params = {**self._query_params, "fields": "fastq_md5", "accession": term}
        response_data = self._get_data(
            term=term,
            params=params,
            error_message="An error occurred when getting md5s from ENA API",
        )

        return response_data[0]['fastq_md5'].split(';')

    def get_urls_and_md5s(
        self, term: str, ftp: bool = False, aspera: bool = False
    ) -> tuple[list[str], list[str]]:
        """
        Returns links and hashes based on the given term

        urls - list of FTP links or IBM Aspera links to download given SRR IDs
        md5s - corresponding hashes to check downloaded files
        """
        if ftp + aspera != 1:
            raise ValueError("Either ftp of aspera flag should be True")

        fields = "fastq_ftp,fastq_md5" if ftp else "fastq_aspera,fastq_md5"
        params = {**self._query_params, "fields": fields, "accession": term}
        response_data = self._get_data(
            term=term,
            params=params,
            error_message="An error occurred getting urls and md5s from ENA API",
        )

        url_type = f"fastq_{'ftp' if ftp else 'aspera'}"

        md5s = response_data[0]['fastq_md5'].split(';')
        if ftp:
            # FTP URLs from ENA do NOT currently include the scheme. Just prepend http://
            # https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html
            urls = [f"http://{uri}" for uri in response_data[0][url_type].split(';')]
        else:
            urls = response_data[0][url_type].split(';')

        return urls, md5s

    def get_urls(self, term: str, ftp: bool = False, aspera: bool = False) -> list[str]:
        """
        Returns links based on the given term

        urls - list of FTP links or IBM Aspera links to download given SRR IDs
        """

        if ftp + aspera != 1:
            raise ValueError("Either ftp of aspera flag should be True")

        fields = "fastq_ftp" if ftp else "fastq_aspera"

        params = {**self._query_params, "fields": fields, "accession": term}
        response_data = self._get_data(
            term=term, params=params, error_message="An error occurred getting urls from ENA API"
        )

        url_type = f"fastq_{'ftp' if ftp else 'aspera'}"

        if ftp:
            # FTP URLs from ENA do NOT currently include the scheme. Just prepend http://
            # https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html
            urls = [f"http://{uri}" for uri in response_data[0][url_type].split(';')]
        else:
            urls = response_data[0][url_type].split(';')

        return urls

    def get_read_count(self, term: str) -> int:
        """Return total count of lines that should be in a file in order to check it is okay."""

        params = {**self._query_params, "fields": "read_count", "accession": term}
        response_data = self._get_data(
            term=term,
            params=params,
            error_message="An error occurred getting read count from ENA API",
        )

        total_spots = int(response_data[0]['read_count'])

        return total_spots

    def _get_data(self, term: str, params: dict[str, str], error_message: str) -> list[th.JsonDict]:
        try:
            response_data = self._get_json(params=params)
        except RequestException as err:
            logger.exception(err)
            logger.error("%s. Accession: %s", error_message, term)
            raise ENAClientError

        if not response_data:
            logger.error("ENA API returned no data for the accession: %s. Cannot proceed", term)
            raise ENAClientError

        return response_data

    def _base_get_json(
        self, params: dict[str, str], url: tp.Optional[str] = ""
    ) -> list[th.JsonDict]:
        """General get method."""
        logger.debug(
            "Querying ENA API with parameters: %s",
            ", ".join([f"{key}={value}" for key, value in params.items()]),
        )
        response = requests.get(url or self._filereport_url, params=params)
        response.raise_for_status()
        if response.status_code == 204:  # ENA API returns 204 instead of 404
            return []
        return response.json()
