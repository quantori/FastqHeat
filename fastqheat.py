import argparse
import logging
import os
import re
import ssl

import requests
import urllib3

from download import download_run_aspc, download_run_fasterq_dump, download_run_ftp
from study_info.get_sra_study_info import get_run_uid

SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(
    r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$'
)


def _handle_f_method(term, out):
    if SRR_PATTERN.search(term) is not None:
        accession = term
        success = download_run_ftp(accession, term, out)

        if not success:
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_ftp(accession, term, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)

    elif SRP_PATTERN.search(term) is not None:
        accession_list, total_spots = get_run_uid(term)

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
    if SRR_PATTERN.search(term) is not None:
        accession = term
        success = download_run_aspc(accession, term, out)

        if not success:
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_aspc(accession, term, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)

    if SRP_PATTERN.search(term) is not None:
        accession_list, total_spots = get_run_uid(term)

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
    if SRR_PATTERN.search(term) is not None:
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

    if SRP_PATTERN.search(term) is not None:
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
