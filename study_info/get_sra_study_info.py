import asyncio
import json
import logging
import os
from xml.etree import ElementTree

import aiohttp
import pandas as pd
import requests
import yaml

DB = 'sra'
ESEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
EFETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'


def get_webenv_and_query_key_with_total_list(term):
    """
    Get Webenv and query key from Esearch to communicate results to Efetch
    about the full list of Run Accessions from the given
    Study/Sample/Experiment/Submission Accession

    Parameters
    ----------
    term: str
            a string like "SRP...."

    Returns
    -------
    tuple
        a tuple of Webenv and query_key about the full list of Run Accessions
    """
    if os.environ.get('API_KEY') is None:
        response = requests.get(
            ESEARCH_URL,
            params={
                'db': DB,
                'term': term,
                'usehistory': 'y',
            }
        )
    else:
        response = requests.get(
            ESEARCH_URL,
            params={
                'db': DB,
                'term': term,
                'usehistory': 'y',
                'api_key': os.environ.get('API_KEY'),
            }
        )
    logging.info(response)
    root = ElementTree.fromstring(response.text)
    query_key = root[3].text
    webenv = root[4].text
    count = int(root[0].text)

    if count > 0:
        logging.info('eSearchResult has been downloaded')
        return webenv, query_key
    elif count == 0:
        logging.error('You send incorrect SRA Study identifier (term)')
        exit(0)


def get_webenv_and_query_key_with_skipped_list(term, skip_list):
    """
    Get Webenv and query key from Esearch to communicate results to Efetch
    about the list of Run Accessions without skipped list from the given 
    Study/Sample/Experiment/Submission Accession

    Parameters
    ----------
    term: str
            a string like "SRP...."
    skip_list: list
            a list of Run Accessions that should be skipped from the full list

    Returns
    -------
    tuple
        a tuple of Webenv and query_key about the Run Accessions
    """
    skip = term + '[All Fields] NOT ' + '[All Fields] NOT '.join(skip_list)
    if os.environ.get('API_KEY') is None:
        response = requests.get(
            ESEARCH_URL,
            params={
                'db': DB,
                'term': skip,
                'usehistory': 'y',
            }
        )
    else:
        response = requests.get(
            ESEARCH_URL,
            params={
                'db': DB,
                'term': skip,
                'usehistory': 'y',
                'api_key': os.environ.get('API_KEY'),
            }
        )
    logging.info(response)
    root = ElementTree.fromstring(response.text)
    query_key = root[3].text
    webenv = root[4].text
    count = int(root[0].text)

    if count > 0:
        logging.info('eSearchResult has been downloaded')
        return webenv, query_key
    elif count == 0:
        logging.error('You send incorrect SRA Study identifier (term)')
        exit(0)


def show_tree(tree):
    """
    Show lxml-tree
    Parameters
    ----------
    tree: elementTree

    Returns
    -------

    """

    from bs4 import BeautifulSoup

    try:
        tt = tree.text
        soup = BeautifulSoup(tt, features="xml")

        sp = soup.prettify()
        print(sp)
    except Exception as e:
        logging.error(e)
        logging.error("Cannot parse lxml tree from sra db")


async def get_total_spot(session, accession):
    url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields=run_accession,read_count&format=json'

    async with session.get(url) as response:
        result_data = await response.json()
        result = result_data[0]['read_count']
        return int(result)


def get_total_spots_with_only_list(only_list):
    try:
        async def main():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for accession in only_list:
                    task = asyncio.ensure_future(get_total_spot(
                                                session,
                                                accession)
                                                )
                    tasks.append(task)

                total_spots = await asyncio.gather(*tasks)
            return total_spots

        x = asyncio.run(main())
        return x
    except TypeError as e:
        logging.error(e)
        return []


def get_run_uid_with_only_list(only_list):
    """
    Get the Run UID by specifying Run Accessions from the only list
    that user provided
    This will be used only when user desires to view lxml
    file with all Run data

    Parameters
    ----------
    only_list: list
            a list of specific Run Accessions

    Returns
    -------
        tuple
            a tuple of list of Run Accessions and list of total
            spots of each Run Accession
    """
    # Limitation is 200 UIDs
    SRRs = []
    total_spots = []
    if os.environ.get('API_KEY') is None:
        response = requests.get(
            EFETCH_URL,
            params={
                'db': DB,
                'id': ','.join(only_list),
            }
        )
    else:
        response = requests.get(
            EFETCH_URL,
            params={
                'db': DB,
                'id': ','.join(only_list),
                'api_key': os.environ.get('API_KEY'),
            }
        )
    logging.debug(response.text)
    show_tree(response)
    root = ElementTree.fromstring(response.text)
    for elem in root.iter():
        if elem.tag == 'RUN':
            logging.debug(elem.attrib)
            SRRs.append(elem.attrib['accession'])
            total_spots.append(int(elem.attrib['total_spots']))
    logging.info('List of runs with only: {}'.format(SRRs))
    return SRRs, total_spots
print(get_run_uid_with_only_list(["fasgvargvargfs", 'vhlhv l ']))

def get_run_uid_with_no_exception(webenv, query_key):
    """
    Get the Run UID by using Webenv and query key retrieved from
    Esearch results

    Parameters
    ----------
    webenv: str
        Web environment string returned from a previous ESearch
    query_key: str
        String query key returned by a previous ESearch

    Returns
    -------
        tuple
            a tuple of list of Run Accessions and list of total
            spots of each Run Accession
    """

    SRRs = []
    total_spots = []
    if os.environ.get('API_KEY') is None:
        response = requests.get(
            EFETCH_URL,
            params={
                'db': DB,
                'Webenv': webenv,
                'query_key': query_key,
            }
        )
    else:
        response = requests.get(
            EFETCH_URL,
            params={
                'db': DB,
                'Webenv': webenv,
                'query_key': query_key,
                'api_key': os.environ.get('API_KEY'),
            }
        )
    logging.debug(response.text)
    show_tree(response)
    root = ElementTree.fromstring(response.text)
    for elem in root.iter():
        if elem.tag == 'RUN':
            logging.debug(elem.attrib)
            SRRs.append(elem.attrib['accession'])
            total_spots.append(int(elem.attrib['total_spots']))
    logging.info('List of runs: {}'.format(SRRs))
    return SRRs, total_spots


def get_run_uid_with_total_list(term, method):
    """
    Get the Run UIDs using Study/Sample/Experiment/Submission Accession, which
    will be used to retrieve ENA File report with all Run Accessions and total
    spots

    Parameters
    ----------
    term: str
            a string like "SRP...."
    method: str
            a string about which method is used for data retrieval

    Returns
    -------
        tuple
            a tuple of list of Run Accessions and list of total
            spots of each Run Accession
    """

    SRRs = []
    total_spots = []
    if method == 'q':
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession,read_count&format=json'
        response = requests.get(url)
        for i in range(0, len(response.json())):
            SRRs.append(response.json()[i]['run_accession'])
            total_spots.append(int(response.json()[i]['read_count']))
    else:
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession&format=json'
        response = requests.get(url)
        SRRs = [response.json()[i]['run_accession']
                for i in range(0, len(response.json()))]
    logging.info('List of total runs: {}'.format(SRRs))
    return SRRs, total_spots


def get_run_uid_with_skipped_list(term, skip_list, method):
    """
    Get the Run UIDs using Study/Sample/Experiment/Submission Accession, which
    will be used to retrieve ENA File report with all Run Accessions and total
    spots except those Run Accessions specified in skipped list by user

    Parameters
    ----------
    term: str
            a string like "SRP...."
    skip_list: list
            a list of Run Accessions that should be skipped
    method: str
            a string about which method is used for data retrieval

    Returns
    -------
        tuple
            a tuple of list of Run Accessions and list of total
            spots of each Run Accession
    """

    SRRs = []
    total_spots = []
    if method == 'q':
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession,read_count&format=json'
        response = requests.get(url)
        for i in range(0, len(response.json())):
            if response.json()[i]['run_accession'] not in set(skip_list):
                SRRs.append(response.json()[i]['run_accession'])
                total_spots.append(response.json()[i]['read_count'])
        logging.debug('Skip list: {}'.format(skip_list))
        logging.info('List of runs without skipped: {}'.format(SRRs))
    else:
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession&format=json'
        response = requests.get(url)
        SRRs = [response.json()[i]['run_accession']
                for i in range(0, len(response.json()))]
        logging.debug('Total list: {}'.format(SRRs))
        SRRs = list(set(SRRs) - set(skip_list))
        logging.debug('Skip list: {}'.format(skip_list))
        logging.info('List of runs without skipped: {}'.format(SRRs))

    return SRRs, total_spots


async def get_accession_metadata(session, accession, value):
    url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields={value}&format=json'

    async with session.get(url) as response:
        result_data = await response.json()
        result_data, = result_data
        return result_data


def get_full_metadata(accession_list, value):
    try:
        async def main():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for accession in accession_list:
                    task = asyncio.ensure_future(get_accession_metadata(
                                                                        session,
                                                                        accession,
                                                                        value))
                    tasks.append(task)

                metadata = await asyncio.gather(*tasks)
                return metadata
        x = asyncio.run(main())
        return x
    except TypeError as e:
        logging.error(e)
        exit(0)


def download_metadata(data, ff, term, out):
    """
    Download metadata retrieved from ENA File report as a file of
    3 possible file formats: CSV, JSON, YAML

    Parameters
    ----------
    data: list
            a list of reports returned in JSON format
    ff: str
            a string of file format
    term: str
            a string like "SRP...."
    out: str
            path to the directory

    Returns
    -------
    """

    if ff == "c":
        df = pd.DataFrame(data)
        df.to_csv(f"{out}/{term}_metadata.csv", index=False)
    elif ff == "j":
        with open(f"{out}/{term}_metadata.json", 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    elif ff == "y":
        with open(f"{out}/{term}_metadata.yaml", 'w') as yml:
            yaml.dump(data, yml, allow_unicode=True)
