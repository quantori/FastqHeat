import logging
import os

import requests

from study_info.check_result import check_loaded_run, md5_checksum


def download_run_fasterq_dump(accession, term, total_spots, out):

    """
    Download the run from from NCBI's Sequence Read Archive (SRA)
    using fasterq_dump and check completeness of downloaded
    fastq file

    Parameters
    ----------
    term: str
            a string of Study Accession
    terms: list
            a list of Study Accessions from provided .txt file
            this parameter can be empy if single accession is provided
    run: str
            a string of Run Accession
    out: str
            The output directory
    total_spots: int
            Number of total spots of each Run Accession

    Returns
    -------
    bool
        True if run was correctly downloaded, otherwise- False
    """
    download_bash_command = f"fasterq-dump {accession} -O {out}/{term} -p"
    logging.debug(download_bash_command)
    logging.info('Try to download %s file', accession)
    os.system(download_bash_command)
    # check completeness of the file and return boolean
    correctness = check_loaded_run(
        run_accession=accession, path=f"{out}/{term}", needed_lines_cnt=total_spots
    )
    if correctness:
        logging.info("")
        os.system(f"gzip {term}/{accession}*")
        logging.info("%s FASTQ file has been zipped", accession)
    return correctness


def download_run_ftp(accession, term, out):
    """
    Download the run from from European Nucleotide Archive (ENA)
    using FTP and check completeness of downloaded
    gunzipped fastq file

    Parameters
    ----------
    term: str
            a string of Study Accession
    terms: list
            a list of Study Accessions from provided .txt file
            this parameter can be empy if single accession is provided
    run: str
            a string of Run Accession
    out: str
            The output directory

    Returns
    -------
    bool
        True if run was correctly downloaded, otherwise- False
    """
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields=fastq_ftp,fastq_md5&format=json"
    response = requests.get(url)
    ftps = response.json()[0]['fastq_ftp'].split(';')
    md5s = response.json()[0]['fastq_md5'].split(';')
    correctness = []

    for i in range(0, len(ftps)):
        SRR = ftps[i].split('/')[-1]
        md5 = md5s[i]
        bash_command = f"mkdir -p {out}/{term} && curl -L {ftps[i]} -o {out}/{term}/{SRR}"
        logging.debug(bash_command)
        logging.info('Try to download %s file', SRR)
        # execute command in commandline
        os.system(bash_command)
        # check completeness of the file and return boolean
        correctness.append(md5_checksum(SRR, f"{out}/{term}", md5))
    if all(correctness):
        logging.info("Current Run: %s has been successfully downloaded", accession)
    return all(correctness)


def download_run_aspc(accession, term, out):
    """
    Download the run from from European Nucleotide Archive (ENA)
    using Aspera and check completeness of downloaded
    gunzipped fastq file

    Parameters
    ----------
    term: str
            a string of Study Accession
    terms: list
            a list of Study Accessions from provided .txt file
            this parameter can be empy if single accession is provided
    run: str
            a string of Run Accession
    out: str
            The output directory

    Returns
    -------
    bool
        True if run was correctly downloaded, otherwise- False
    """
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields=fastq_aspera,fastq_md5&format=json"
    response = requests.get(url)
    asperas = response.json()[0]['fastq_aspera'].split(';')
    md5s = response.json()[0]['fastq_md5'].split(';')
    correctness = []

    for i in range(0, len(asperas)):
        SRR = asperas[i].split('/')[-1]
        md5 = md5s[i]
        bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{asperas[i]} . && mkdir -p {out}/{term} && mv {SRR} {out}/{term}'
        logging.debug(bash_command)
        logging.info('Try to download %s file', SRR)
        # execute command in commandline
        os.system(bash_command)
        # check completeness of the file and return boolean
        correctness.append(md5_checksum(SRR, f"{out}/{term}", md5))

    if all(correctness):
        logging.info("Current Run: %s has been successfully downloaded", accession)
        return True
    else:
        return False
