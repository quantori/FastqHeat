import argparse
import logging
import os
import re
import ssl
import urllib3
import subprocess
from pathlib import Path

import requests

import metadata
from check import check_loaded_run, md5_checksum

SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')
USABLE_CPUS_COUNT = len(os.sched_getaffinity(0))


def download_run_fasterq_dump(accession, term, output_directory):
    total_spots = metadata.get_read_count(accession)

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
    ftps, md5s = metadata.get_urls_and_md5s(accession)

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

    asperas, md5s = metadata.get_urls_and_md5s(accession)

    for aspera, md5 in zip(asperas, md5s):
        SRR = aspera.split('/')[-1]
        bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{aspera} . && mkdir -p {out}/{term} && mv {SRR} {out}/{term}'  # noqa: E501 line too long - will be fixed in next PRs
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


method_to_download_function = {
    "f": download_run_ftp,
    "a": download_run_aspc,
    "q": download_run_fasterq_dump,
}


def _make_accession_list(term_: str) -> list[str]:
    """Get an accession list based on pattern of the given term."""
    if SRR_PATTERN.search(term_):
        accession_list = [term_]
    elif SRP_PATTERN.search(term_):
        accession_list = metadata.get_srr_ids_from_srp(term_)
    else:
        raise ValueError(f"Unknown pattern: {term_}")

    return accession_list


def handle_methods(term_: str, method_: str, out) -> bool:
    """Runs specific download function based on the given method."""
    states = []
    try:
        download_function = method_to_download_function[method_]
    except KeyError:
        raise ValueError(f"Unknown method: {method_}")

    accession_list = _make_accession_list(term_)

    for accession in accession_list:
        states.append(download_function(accession, out))

    return all(states)


class TermParser:
    """
    Provides a method for parsing terms from a string.

    A string can represent a singular term or a *.txt file with a few terms.
    """

    def __init__(self, directory: str):
        self.terms = []
        self.directory = directory

    @staticmethod
    def _parse_terms_from_file(filename: str) -> list[str]:
        with open(f"{out_dir}/{filename}", "r") as file:
            return [line.strip() for line in file]

    def parse_from_input(self, input_string: str):
        if not input_string:
            logging.error('Empty term.')
            raise ValueError

        if input_string.endswith('.txt'):
            self.terms = self._parse_terms_from_file(input_string)
        elif "." not in input_string:
            self.terms = [input_string]
        else:
            logging.error('Use either correct term or only .txt file format.')
            raise ValueError

        return self.terms


if __name__ == "__main__":
    # For debugging use
    # term = 'SRP150545'  #   6 files more than 2-3Gb each
    # term = 'SRP163674'  # 129 files, 2-8 Mb each (ex of double stranded SRR7969890)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "term",
        help=(
            "The name of SRA Study identifier, looks like SRP... or ERP... or DRP...  "
            "or .txt file name which includes multiple SRA Study identifiers",
        ),
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
        help=(
            "Choose different type of methods that should be used for data retrieval: "
            "Aspera (a), FTP (f), fasterq_dump (q). By default it is fasterq_dump (q)"
        ),
        default='q',
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")

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

    terms = TermParser(out_dir).parse_from_input(args.term)

    try:
        for term in terms:
            if handle_methods(term, method, out_dir):
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
        print("Incorrect parameters were provided to tool. Try again with correct ones from ENA.")
        exit(0)
    except KeyboardInterrupt:
        print("Session was interrupted!")
        exit(0)
    except BaseException as e:
        logging.error(e)
        print("Something went wrong! Exiting the system!")
        exit(0)
