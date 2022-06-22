import argparse
import logging
import os
import re
import ssl
import urllib3
import subprocess
from pathlib import Path

import requests

from check import check_loaded_run, md5_checksum
from metadata import get_run_uid

SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')
USABLE_CPUS_COUNT = len(os.sched_getaffinity(0))

def handle_methods(term, method, out):
    # accessions = []

    if SRR_PATTERN.search(term):
        accession = term  # append(?)
    elif SRP_PATTERN.search(term):
        accession_list = get_run_uid(term, approach="srp")

    # for accession in accessions:
    if method == "f":
        success = download_run_ftp(accession, term, out)

        if not success:
            """
            Заменить на библиотеку
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_fasterq_dump(accession, term, read_count, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)
            """

    elif method == "a":
        success = download_run_aspc(accession, term, out)

        if not success:
            """
            Заменить на библиотеку
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_fasterq_dump(accession, term, read_count, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)
            """
    elif method == "q":
        success = download_run_fasterq_dump(accession, term, out)

        if not success:
            """
            Заменить на библиотеку
            logging.warning("Failed to download %s. Trying once more.", accession)
            success = download_run_fasterq_dump(accession, term, read_count, out)
            if success:
                logging.info("The second try was successful!")
            else:
                logging.error("Failed the second try. Skipping the %s", accession)
            """

def download_run_fasterq_dump(accession, term, output_directory, *, core_count):

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
    total_spots = get_run_uid(accession, approach="sra")

    output_directory = Path(output_directory, term)
    logging.info('Trying to download %s file', accession)
    subprocess.run(
        ['fasterq-dump', accession, '-O', output_directory, '-p', '--threads', str(core_count)],
        check=True,
    )
    # check completeness of the file and return boolean
    correctness = check_loaded_run(
        run_accession=accession, path=output_directory, needed_lines_cnt=total_spots
    )
    if correctness:
        fastq_files = list(output_directory.glob(f'{accession}*.fastq'))
        logging.info("Compressing FASTQ files for %s in %s", accession, output_directory)
        subprocess.run(['pigz', '--processes', str(core_count), *fastq_files], check=True)
        logging.info("FASTQ files for %s have been zipped", accession)

    return correctness


def download_run_ftp(accession, term, out):
    correctness = []
    md5s, ftps, _,  = get_run_uid(accession, approach="ena")

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
    correctness = []

    md5s, _, asperas = get_run_uid(accession, approach="ena")

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


if __name__ == "__main__":
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
