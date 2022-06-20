import json
import logging

import requests

def get_run_uid(term, method):
    if method == "srp":
        _get_run_srp(term)
    elif method == "ena":
        _get_run_ena(term)
    elif method == "sra":
        _get_run_sra(term)
    elif method == "check":
        _get_run_check(term)


def _get_run_srp(term):
    SRRs = []
    try:
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession&format=json'
        response = requests.get(url)
        response_data = response.json()
        for data in response_data:
            SRRs.append(data['run_accession'])
    except json.decoder.JSONDecodeError as e:
        logging.error(e)
        exit(0)
    else:
        return SRRs


def _get_run_ena(term):
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=fastq_ftp,fastq_aspera,fastq_md5&format=json"
    response = requests.get(url)
    md5s = response.json()[0]['fastq_md5'].split(';')
    ftps = response.json()[0]['fastq_ftp'].split(';')
    asperas = response.json()[0]['fastq_aspera'].split(';')

    return md5s, ftps, asperas


def _get_run_sra(term):
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=read_count&format=json"
    response = requests.get(url)
    total_spots = int(response.json()[0]['read_count'])

    return total_spots


def _get_run_check(term):
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=fastq_md5,read_count&format=json"
    response = requests.get(url)
    md5s = response.json()[0]['fastq_md5'].split(';')
    total_spots = int(response.json()[0]['read_count'])

    return md5s, total_spots
