import argparse
import json
import logging
import os
import re
import ssl

import requests
import urllib3

from study_info.check_result import check_loaded_run, md5_checksum

SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')


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

    for ftp, md5 in zip(ftps, md5s):
        SRR = ftp.split('/')[-1]
        bash_command = f"mkdir -p {out}/{term} && curl -L {ftp} -o {out}/{term}/{SRR}"

        logging.debug(bash_command)
        logging.info('Try to download %s file', SRR)
        # execute command in commandline
        os.system(bash_command)
        # check completeness of the file and return boolean
        correctness.append(md5_checksum(SRR, f"{out}/{term}", md5))

    if all(correctness):
        logging.info("Current Run: %s has been successfully downloaded", accession)
        return True
    return False


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

    for aspera, md5 in zip(asperas, md5s):
        SRR = aspera.split('/')[-1]
        bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{aspera} . && mkdir -p {out}/{term} && mv {SRR} {out}/{term}'
        logging.debug(bash_command)
        logging.info('Try to download %s file', SRR)
        # execute command in commandline
        os.system(bash_command)
        # check completeness of the file and return boolean
        correctness.append(md5_checksum(SRR, f"{out}/{term}", md5))

    if all(correctness):
        logging.info("Current Run: %s has been successfully downloaded", accession)
        return True
    return False


def _handle_f_method(term, out):
    if SRR_PATTERN.search(term):
        accession = term
        success = download_run_ftp(accession, term, out)

        if not success:
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_ftp(accession, term, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)

    elif SRP_PATTERN.search(term):
        accession_list, _ = get_run_uid(term)

        for accession in accession_list:
            success = download_run_ftp(accession, term, out)

            if not success:
                logging.warning("Failed to download %s. Trying once more.", accession)
                success = download_run_ftp(accession, term, out)
                if success:
                    logging.info("The second try was successful!")
                else:
                    logging.error("Failed the second try. Skipping the %s", accession)


def _handle_a_method(term, out):
    if SRR_PATTERN.search(term):
        accession = term
        success = download_run_aspc(accession, term, out)

        if not success:
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_aspc(accession, term, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)

    if SRP_PATTERN.search(term):
        accession_list, _ = get_run_uid(term)

        for accession in accession_list:
            success = download_run_aspc(accession, term, out)

            if not success:
                logging.warning("Failed to download %s. Trying once more.", accession)
                success = download_run_aspc(accession, term, out)
                if success:
                    logging.info("The second try was successful!")
                else:
                    logging.error("Failed the second try. Skipping the %s", accession)


def _handle_q_method(term, out):
    if SRR_PATTERN.search(term):
        accession = term
        bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields=read_count&format=json"
        response = requests.get(bash_command)
        total_spots = int(response.json()[0]['read_count'])
        success = download_run_fasterq_dump(accession, term, total_spots, out)

        if not success:
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_fasterq_dump(accession, term, total_spots, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)

    if SRP_PATTERN.search(term):
        accession_list, total_spots = get_run_uid(term)

        for accession, read_count in zip(accession_list, total_spots):
            success = download_run_fasterq_dump(accession, term, read_count, out)

            if not success:
                logging.warning("Failed to download %s. Trying once more.", accession)
                success = download_run_fasterq_dump(accession, term, read_count, out)
                if success:
                    logging.info("The second try was successful!")
                else:
                    logging.error("Failed the second try. Skipping the %s", accession)


def handle_methods(term, method, out):
    if method == "f":
        _handle_f_method(term, out)
    elif method == "a":
        _handle_a_method(term, out)
    elif method == "q":
        _handle_q_method(term, out)


if __name__ == "__main__":
    """
    This script helps to download runs using different methods.

    How it works.

        Parameters:

    positional arguments:
            term              The name of Study/Sample/Experiment/Submission
                              Accession or the name of the file with
                              Study Accessions

    optional arguments:
        -h, --help            show this help message and exit
        -L, --log             To point logging level (debug, info, warning,
                              error. "info" by default)
        -M, --method          Method of downloading fastq or fastq.gz file.
                              There are 3 options for downloading data: FTP,
                              Aspera and fasterq_dump. To use Aspera specify
                              after -M command a, to use FTP specify f, and
                              for fasterq_dump specify q.
        -O, --out             Output directory

    Ex 1: download all into the directory
                        python3 fastqheat.py SRP163674 --out /home/user/tmp
    Ex 2: download all using Aspera CLI
                        python3 fastqheat.py SRP163674 -M a
    Ex 3: download runs of multiple study accessions from .txt file using fasterq_dump
                        python3 fastqheat.py *.txt -M q
    Ex 4: download all files from Sample Accession
                        python3 fastqheat.py SAMN10181503



    """
    # For debugging use
    # term = 'SRP150545'  #   6 files more than 2-3Gb each
    # term = 'SRP163674'  # 129 files, 2-8 Mb each (ex of double stranded SRR7969890)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "term",
        help="The name of SRA Study identifier, looks like SRP... or ERP... or DRP...  or .txt file name which includes multiple SRA Study identifiers",
    )
    parser.add_argument(
        "-L",
        "--log",
        dest="log_level",
        help="Logging level",
        choices=["debug", "info", "warning", "error"],
        default="info",
    )
    parser.add_argument("-O", "--out", help="Output directory", default=".")
    parser.add_argument(
        "-M",
        "--method",
        help="Choose different type of methods that should be used for data retrieval: Aspera (a), FTP (f), fasterq_dump (q). By default it is fasterq_dump (q)",
        default='q',
    )
    args = parser.parse_args()

    # choose method type
    if args.method:
        method = args.method
    else:
        logging.error('Choose any method for data retrieval')
        exit(0)

    try:
        if method == 'q':
            fd_version = os.popen("fasterq-dump --version").read()
            tool = "fasterq+dump"
        elif method == 'a':
            fd_version = os.popen("aspera --version").read()
            tool = "Aspera CLI"
        else:
            fd_version = ''
            tool = ''
    except IOError as e:
        logging.error(e)
        logging.error("SRA Toolkit/Aspera CLI not installed or not pointed in path")
        exit(0)
    parser.add_argument(
        '--version', action='version', version=f'{tool} which use {fd_version} version'
    )

    out_dir = "."
    if args.out:
        if os.path.isdir(args.out):
            out_dir = args.out
        else:
            logging.error('Pointed directory does not exist.')
            exit(0)

    if args.term:
        term = args.term
        if term.endswith('.txt'):
            with open(f"{out_dir}/{term}", "r") as file:
                terms = [line.strip() for line in file]
        elif '.' not in term:
            terms = []
        else:
            logging.error('Use either correct term or only .txt file format.')
            exit(0)
    else:
        logging.error('Use correct term name.')
        exit(0)

    try:
        logging.basicConfig(
            level=args.log_level.upper(), format='[level=%(levelname)s]: %(message)s'
        )

        if not terms:
            handle_methods(term, method, out_dir)
            logging.info("All runs were loaded.")
        else:
            for term in terms:
                handle_methods(term, method, out_dir)
                logging.info("All runs were loaded.")
    except ValueError as e:
        logging.error(e)
        print("Unexpected exit")
        exit(0)
    except (
        requests.exceptions.SSLError,
        urllib3.exceptions.MaxRetryError,
        ssl.SSLEOFError,
    ) as e:
        logging.error(e)
        print("Too many requests were made. Exiting system.")
        exit(0)
    except requests.exceptions.ConnectionError as e:
        logging.error(e)
        print(
            "Incorrect parameter(s) was/were provided to tool. Try again with correct ones from ENA."
        )
        exit(0)
    except KeyboardInterrupt:
        print("Session was interrupted!")
        exit(0)
    except BaseException as e:
        logging.error(e)
        print("Something went wrong! Exiting the system!")
        exit(0)
