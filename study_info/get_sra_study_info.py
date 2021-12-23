import logging
from xml.etree import ElementTree
import requests

DB = 'sra'
ESEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
EFETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'


def get_webenv_and_query_key_with_total_list(term):
    """
    Get the list of run identifiers in this SRA study.
    Parameters
    ----------
    term: str
            a string like "SRP...."

    Returns
    -------

    """
    response = requests.get(
        ESEARCH_URL,
        params={
            'db': DB,
            'term': term,
            'usehistory': 'y'
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
    Get the list of run identifiers in this SRA study.
    Parameters
    ----------
    term: str
            a string like "SRP...."

    Returns
    -------

    """
    skip = term + '[All Fields] NOT ' + '[All Fields] NOT '.join(skip_list)
    response = requests.get(
        ESEARCH_URL,
        params={
            'db': DB,
            'term': skip,
            'usehistory': 'y'
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


def get_run_uid_with_only_list(only_list):
    """
    Get the Run UID by its Id
    Parameters
    ----------
    id: object
        Run identifier
    show: bool
        show or hide lxml tree of response
    Returns
    -------
        str
    """

    # Get the lxml tree when show is yes
    # Limitation is 200 UIDs for eFetch id property
    SRRs = []
    total_spots = []
    response = requests.get(
        EFETCH_URL,
        params={
            'db': DB,
            'id': ','.join(only_list)
        }
    )
    logging.debug(response.text)
    show_tree(response)
    root = ElementTree.fromstring(response.text)
    for elem in root.iter():
        if elem.tag == 'RUN':
            logging.debug(elem.attrib)
            SRRs.append(elem.attrib['accession'])
            total_spots.append(elem.attrib['total_spots'])

    return SRRs, total_spots


def get_run_uid_with_no_exception(webenv, query_key):
    """
    Get the Run UID by its Id
    Parameters
    ----------
    id: object
        Run identifier
    show: bool
        show or hide lxml tree of response
    Returns
    -------
        str
    """

    # Get the lxml tree when show is yes
    # Limitation is 200 UIDs for eFetch id property
    SRRs = []
    total_spots = []
    response = requests.get(
        EFETCH_URL,
        params={
            'db': DB,
            'Webenv': webenv,
            'query_key': query_key
        }
    )
    logging.debug(response.text)
    show_tree(response)
    root = ElementTree.fromstring(response.text)
    for elem in root.iter():
        if elem.tag == 'RUN':
            logging.debug(elem.attrib)
            SRRs.append(elem.attrib['accession'])
            total_spots.append(elem.attrib['total_spots'])

    return SRRs, total_spots


def get_run_uid_with_total_list(term, method):
    """
    Get the Run UID by its Id
    Parameters
    ----------
    id: object
        Run identifier
    show: bool
        show or hide lxml tree of response
    Returns
    -------
        str
    """

    # Get the lxml tree when show is yes
    # Limitation is 200 UIDs for eFetch id property
    # Retrieve data using ENA
    SRRs = []
    total_spots = []
    if method == 'q':
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession,read_count&format=json'
        response = requests.get(url)
        for i in range(0, len(response.json())):
            SRRs.append(response.json()[i]['run_accession'])
            total_spots.append(response.json()[i]['read_count'])
    else:
        url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={term}&result=read_run&fields=run_accession&format=json'
        response = requests.get(url)
        SRRs = [response.json()[i]['run_accession']
                for i in range(0, len(response.json()))]
    return SRRs, total_spots


def get_run_uid_with_skipped_list(term, skip_list, method):
    """
    Get the Run UID by its Id
    Parameters
    ----------
    id: object
        Run identifier
    show: bool
        show or hide lxml tree of response
    Returns
    -------
        str
    """

    # Get the lxml tree when show is yes
    # Limitation is 200 UIDs for eFetch id property
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

    # If we are here it means something wrong with info about experiment
    # logging.error('There is not RUN info by this UID')
    # exit(0)
