import logging
import os
import requests

sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries = 20)
sess.mount('http://', adapter)


def download_run_fasterq_dump(run, out):
    """
    Download the run from database using fasterq_dump and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """

    download_bash_command = "fasterq-dump " + run + " -O " + out
    logging.debug(download_bash_command)

    logging.info('Try to download {} file'.format(run))
    # execute command in commandline
    os.system(download_bash_command)
    logging.info('A try was finished.')


def download_run_ftp(run, out):
    """
    Download the run from database using FTP and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """
    bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={run}&result=read_run&fields=fastq_ftp&format=json"
    response = requests.get(bash_command)
    ftps = response.json()[0]['fastq_ftp'].split(';')
    download_bash_command = ''
    for ftp in ftps:
        SRR = ftp.split('/')[-1]
        download_bash_command = "curl -L " + ftp + " -o " + out + "/" + SRR
        logging.debug(download_bash_command)

        logging.info('Try to download {} file'.format(run))
    # execute command in commandline
        os.system(download_bash_command)
    logging.info('A try was finished.')


def download_run_aspc(run, out):
    """
    Download the run from database using Aspera and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """
    bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={run}&result=read_run&fields=fastq_aspera&format=json"
    response = requests.get(bash_command)
    asperas = response.json()[0]['fastq_aspera'].split(';')

    for aspera in asperas:
        if out != '.':
            SRR = SRR = aspera.split('/')[-1]
            download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{aspera} . && mv {SRR} {out}/{SRR}'
        else:
            download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{aspera} .'

        logging.debug(download_bash_command)

        logging.info('Try to download {} file'.format(run))
        # execute command in commandline
        os.system(download_bash_command)
    logging.info('A try was finished.')
