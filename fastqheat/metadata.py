import json
import logging

import requests

BASE_URL = (
    "https://www.ebi.ac.uk/ena/portal/api/filereport?accession={}&result=read_run&format=json"
)


def get_srr_ids_from_srp(term: str) -> list[str]:
    """Returns list of SRR(ERR) IDs based on the given SRP(ERP) ID."""

    srr_ids = []
    try:
        url = f"{BASE_URL.format(term)}&fields=run_accession"
        response = requests.get(url)
        response_data = response.json()
        for data in response_data:
            srr_ids.append(data['run_accession'])
    except json.decoder.JSONDecodeError as e:
        logging.error(e)
        exit(0)
    else:
        return srr_ids


def get_urls_and_md5s(term: str, ftp=False, aspera=False) -> tuple[list[str], list[str]]:
    """
    Returns links and hashes based on the given term

    urls - list of FTP links or IBM Aspera links to download given SRR IDs
    md5s - corresponding hashes to check downloaded files
    """
    if ftp + aspera != 1:
        raise ValueError("Either ftp of aspera flag should be True")

    fields = "fastq_ftp,fastq_md5" if ftp else "fastq_aspera,fastq_md5"

    url = f"{BASE_URL.format(term)}&fields={fields}"
    response = requests.get(url)
    response.raise_for_status()

    url_type = f"fastq_{'ftp' if ftp else 'aspera'}"

    md5s = response.json()[0]['fastq_md5'].split(';')
    if ftp:
        # FTP URLs from ENA do NOT currently include the scheme. Just prepend http://
        # https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html
        urls = [f"http://{uri}" for uri in response.json()[0][url_type].split(';')]
    else:
        urls = response.json()[0][url_type].split(';')

    return urls, md5s


def get_read_count(term: str) -> int:
    """Return total count of lines that should present in a file in order to check it is okay."""
    url = f"{BASE_URL.format(term)}&fields=read_count"
    response = requests.get(url)
    total_spots = int(response.json()[0]['read_count'])

    return total_spots


def get_run_check(term: str):
    """Returns md5 hashes and total count of a file in order to check if it is okay."""
    url = f"{BASE_URL.format(term)}&fields=fastq_md5,read_count"
    response = requests.get(url)
    md5s = response.json()[0]['fastq_md5'].split(';')
    total_spots = int(response.json()[0]['read_count'])

    return md5s, total_spots
