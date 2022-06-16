import json
import logging

import requests


def get_run_uid(term):
    SRRs = []
    total_spots = []
    try:
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession,read_count&format=json'
        response = requests.get(url)
        response_data = response.json()
        for data in response_data:
            SRRs.append(data['run_accession'])
            total_spots.append(float(data['read_count']))
    except json.decoder.JSONDecodeError as e:
        logging.error(e)
        exit(0)
    else:
        return SRRs, total_spots
