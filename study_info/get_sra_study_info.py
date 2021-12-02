import logging
from xml.etree import ElementTree
import requests

DB = 'sra'
ESEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
EFETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'


def get_retmax(term):
    """
    Get max number of runs in the SRA study
    Parameters
    ----------
    term: str
            a string of SRA Study like "SRP...." / "DRP..." etc

    Returns
    -------
        retmax: int
    """

    response = requests.get(
        ESEARCH_URL,
        params={
            'db': DB,
            'term': term
        }
    )
    logging.info(response)

    root = ElementTree.fromstring(response.text)

    try:
        cnt = int(root[0].text)
        logging.info('Cnt of runs is {}'.format(cnt))
        return cnt
    except ValueError:
        logging.error("Cnt of runs is incorrect. Check that lxml file did not change.")


def get_id_list(term, retmax):
    """
    Get the list of run identifiers in this SRA study.
    Parameters
    ----------
    term: str
            a string like "SRP...."
    retmax: int
            max cnt of runs in the SRA study

    Returns
    -------

    """
    response = requests.get(
        ESEARCH_URL,
        params={
            'db': DB,
            'term': term,
            'retmax': retmax
        }
    )
    logging.info(response)

    root = ElementTree.fromstring(response.text)
    id_list_tree = root[3]    # IdList tag

    id_list = []
    for id in id_list_tree:
        if id.tag == 'Id':
            id_list.append(id.text)

    if len(id_list) > 0:
        logging.info('List of idx downloaded')
        return id_list
    elif len(id_list) == 0:
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


def get_run_uid_by_id(id, show=False):
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

    # Get the whole lxml tree with all info about study
    response = requests.get(
        EFETCH_URL,
        params={
            'db': DB,
            'id': id
        }
    )

    logging.debug(response.text)

    # To show the lxml tree if needed
    if show:
        show_tree(response)

    root = ElementTree.fromstring(response.text)

    # From the lxml tree to get only RUN info
    for elem in root.iter():
        if elem.tag == 'RUN':
            logging.debug(elem.attrib)
            return elem.attrib

    # If we are here it means something wrong with info about experiment
    logging.error('There is not RUN info by this UID')
    exit(0)
