import typing as tp

import requests


class ENAClient:
    """
    Client to work with European Nucleotide Archive public API.

    Swagger: https://www.ebi.ac.uk/ena/portal/api/
    """

    def __init__(self):
        self._base_url = "https://www.ebi.ac.uk/ena/portal/api/filereport"
        self._query_params = {"result": "read_run", "format": "json"}

    def get_srr_ids_from_srp(self, term: str) -> list[str]:
        """Returns list of SRR(ERR) IDs based on the given SRP(ERP) ID."""

        srr_ids = []

        params = {**self._query_params, "accession": term}

        response_data = self._get(params=params)
        for data in response_data:
            srr_ids.append(data['run_accession'])
        return srr_ids

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

        response_data = self._get(params=params)

        url_type = f"fastq_{'ftp' if ftp else 'aspera'}"

        md5s = response_data[0]['fastq_md5'].split(';')
        if ftp:
            # FTP URLs from ENA do NOT currently include the scheme. Just prepend http://
            # https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html
            urls = [f"http://{uri}" for uri in response_data[0][url_type].split(';')]
        else:
            urls = response_data[0][url_type].split(';')

        return urls, md5s

    def get_read_count(self, term: str) -> int:
        """Return total count of lines that should be in a file in order to check it is okay."""

        params = {**self._query_params, "fields": "read_count", "accession": term}
        response_data = self._get(params=params)
        total_spots = int(response_data[0]['read_count'])

        return total_spots

    def get_run_check(self, term: str) -> tuple[list[str], int]:
        """Returns md5 hashes and total count of a file in order to check if it is okay."""
        params = {**self._query_params, "fields": "fastq_md5,read_count", "accession": term}
        response_data = self._get(params=params)
        md5s = response_data[0]['fastq_md5'].split(';')
        total_spots = int(response_data[0]['read_count'])

        return md5s, total_spots

    def _get(self, params: tp.Dict[str, str]):
        """General get method."""
        response = requests.get(url=self._base_url, params=params)
        response.raise_for_status()
        return response.json()
