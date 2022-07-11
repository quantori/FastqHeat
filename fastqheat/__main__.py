import argparse
import logging
import os.path
import re
import ssl
import subprocess
import typing as tp
from pathlib import Path

import backoff
import requests
import urllib3

from fastqheat.check import check_loaded_run, md5_checksum
from fastqheat.config import config
from fastqheat.metadata import ENAClient
from fastqheat.typing_helpers import PathType
from fastqheat.utility import get_cpu_cores_count

SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')
USABLE_CPUS_COUNT = get_cpu_cores_count()

subprocess_run = backoff.on_exception(
    backoff.constant, subprocess.CalledProcessError, max_tries=lambda: config.MAX_RETRIES
)(subprocess.run)


def get_program_version(program_name: str) -> tp.Optional[str]:
    try:
        result = subprocess.run(
            [program_name, '--version'], text=True, capture_output=True, check=True
        )
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr or e.stdout)
        raise
    else:
        output = result.stdout.strip()
        if program_name == 'ascp':
            return output.splitlines()[0]
        return output


@backoff.on_exception(
    backoff.constant,
    subprocess.CalledProcessError,
    max_tries=lambda: config.MAX_RETRIES,
)
def _run_command(args: tp.Any) -> None:
    subprocess.run(args, check=True)


@backoff.on_predicate(backoff.constant, max_tries=lambda: config.MAX_RETRIES)
def download_run_fasterq_dump(
    accession: str, output_directory: PathType, *, core_count: int
) -> bool:
    """

    Download the run from NCBI's Sequence Read Archive (SRA)
    Uses fasterq_dump and check completeness of downloaded fastq file
    Parameters
    ----------
    accession: str
        a string of Study Accession
    output_directory: str
        The output directory
    core_count: int
        Number of cores to utilize
    Returns
    -------
    bool
        True if run was correctly downloaded, otherwise - False
    """
    total_spots = ENAClient().get_read_count(accession)
    accession_directory = Path(output_directory, accession)
    accession_directory.mkdir(parents=True, exist_ok=True)

    logging.info('Trying to download %s file', accession)
    _run_command(
        ['fasterq-dump', accession, '-O', accession_directory, '-p', '--threads', str(core_count)],
    )
    # check completeness of the file and return boolean
    correctness = check_loaded_run(
        run_accession=accession, path=accession_directory, needed_lines_cnt=total_spots
    )
    if correctness:
        fastq_files = list(accession_directory.glob(f'{accession}*.fastq'))
        logging.info("Compressing FASTQ files for %s in %s", accession, accession_directory)
        subprocess.run(['pigz', '--processes', str(core_count), *fastq_files], check=True)
        logging.info("FASTQ files for %s have been zipped", accession)

    return correctness


@backoff.on_exception(
    backoff.constant,
    requests.exceptions.RequestException,
    max_tries=lambda: config.MAX_RETRIES,
)
def _download_file(url: str, output_file_path: Path, chunk_size: int = 10**6) -> None:
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with output_file_path.open('wb') as file:
            for chunk in response.iter_content(chunk_size):
                file.write(chunk)


@backoff.on_predicate(backoff.constant, max_tries=lambda: config.MAX_RETRIES)
def download_run_ftp(accession: str, output_directory: PathType) -> bool:
    """
    Download the run from European Nucleotide Archive (ENA)

    Users FTP and checks completeness of downloaded gunzipped fastq file

    Parameters
    ----------
    accession: str
        a string of Study Accession

    output_directory: str
        The output directory
    Returns
    -------
    bool
        True if run was correctly downloaded, otherwise - False
    """
    ftps, md5s = ENAClient().get_urls_and_md5s(accession, ftp=True)
    successful = True
    accession_directory = Path(output_directory, accession)
    accession_directory.mkdir(parents=True, exist_ok=True)

    for ftp, md5 in zip(ftps, md5s):
        srr = ftp.split('/')[-1]
        logging.info('Trying to download %s file', srr)
        file_path = accession_directory / srr

        _download_file(ftp, file_path)

        # check completeness of the file
        if not md5_checksum(file_path, md5):
            successful = False

    if successful:
        logging.info("Current Run: %s has been successfully downloaded", accession)

    return successful


def download_run_aspc(accession: str, output_directory: PathType) -> bool:
    """
    Download the run from European Nucleotide Archive (ENA)

    Uses Aspera and checks completeness of downloaded gunzipped fastq file

    Parameters
    ----------
    accession: str
        a string of Study Accession
    output_directory: str
            The output directory
    Returns
    -------
    bool
        True if run was correctly downloaded, otherwise - False
    """

    asperas, md5s = ENAClient().get_urls_and_md5s(accession, aspera=True)
    successful = True
    accession_directory = Path(output_directory, accession)
    accession_directory.mkdir(parents=True, exist_ok=True)

    for aspera, md5 in zip(asperas, md5s):
        srr = aspera.split('/')[-1]
        logging.info('Trying to download %s file', srr)

        subprocess_run(
            [
                'ascp',
                '-QT',
                '-l',
                '300m',
                '-P',
                '33001',
                '-i',
                config.PATH_TO_ASPERA_KEY,
                f'era-fasp@{aspera}',
                Path(),
            ],
            check=True,
        )

        file_path = Path(srr).rename(accession_directory / srr)
        # check completeness of the file
        if not md5_checksum(file_path, md5):
            successful = False

    if successful:
        logging.info("Current Run: %s has been successfully downloaded", accession)

    return successful


method_to_download_function: dict[str, tp.Callable[..., bool]] = {
    "f": download_run_ftp,
    "a": download_run_aspc,
    "q": download_run_fasterq_dump,
}


def _make_accession_list(term: str) -> list[str]:
    """Get an accession list based on pattern of the given term."""
    if SRR_PATTERN.search(term):
        accession_list = [term]
    elif SRP_PATTERN.search(term):
        accession_list = ENAClient().get_srr_ids_from_srp(term)
    else:
        raise ValueError(f"Unknown pattern: {term}")

    return accession_list


def handle_methods(term: str, method: str, out: PathType, *, core_count: int) -> list[bool]:
    """Runs specific download function based on the given method."""

    states = []
    try:
        download_function = method_to_download_function[method]
    except KeyError:
        raise ValueError(f"Unknown method: {method}")

    accession_list = _make_accession_list(term)

    if method == 'q':
        for accession in accession_list:
            states.append(download_function(accession, out, core_count=core_count))
    else:
        for accession in accession_list:
            states.append(download_function(accession, out))

    return states


class TermParser:
    """
    Provides a method for parsing terms from a string.

    A string can represent a singular term or a *.txt file with a few terms.
    """

    def __init__(self, directory: str):
        self.terms: list[str] = []
        self.directory = directory

    @staticmethod
    def _parse_terms_from_file(filename: str) -> list[str]:
        with open(filename, "r") as file:
            return [line.strip() for line in file]

    def parse_from_input(self, input_string: str) -> list[str]:
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


def _positive_integer_argument(value: str) -> int:
    converted = int(value)
    if converted <= 0:
        raise ValueError

    return converted


if __name__ == "__main__":
    # For debugging use
    # term = 'SRP150545'  #   6 files more than 2-3Gb each
    # term = 'SRP163674'  # 129 files, 2-8 Mb each (ex of double stranded SRR7969890)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "term",
        help=(
            "The name of SRA Study identifier, looks like SRP... or ERP... or DRP...  "
            "or .txt file name which includes multiple SRA Study identifiers"
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
    parser.add_argument(
        '-c',
        '--cores',
        help='Number of CPU cores to utilise (for subcommands that support parallel execution)',
        default=USABLE_CPUS_COUNT,
        type=_positive_integer_argument,
    )
    parser.add_argument(
        '-r',
        '--retries',
        help='Retry failed requests this number of times',
        type=_positive_integer_argument,
    )
    args = parser.parse_args()

    config.MAX_RETRIES = args.retries
    logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")

    # choose method type
    if args.method:
        method = args.method
    else:
        logging.error('Choose any method for data retrieval')
        exit(0)

    if method == 'q':
        fd_version = get_program_version('fasterq-dump')
        if fd_version is None:
            logging.error('fasterq-dump (part of SRA Toolkit) is not installed or not on PATH')
            exit(0)

        pigz_version = get_program_version('pigz')
        if pigz_version is None:
            logging.error('pigz is not installed or not on PATH')
            exit(0)

        tool = "fasterq+dump"
    elif method == 'a':
        fd_version = get_program_version('ascp')
        if fd_version is None:
            logging.error('Aspera CLI is not installed or not on PATH')
            exit(0)

        tool = "Aspera CLI"
    else:
        fd_version = ''
        tool = ''

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

    total_states = []
    for term in terms:
        try:
            total_states.extend(handle_methods(term, method, out_dir, core_count=args.cores))
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
                "Incorrect parameters were provided to tool. Try again with correct ones from ENA."
            )
            exit(0)
        except KeyboardInterrupt:
            print("Session was interrupted!")
            exit(0)
        except BaseException as e:
            logging.error(e)
            print("Something went wrong! Exiting the system!")
            exit(0)

    logging.info(
        "A total of %d runs were successfully loaded and %d failed to load.",
        len(total_states),
        total_states.count(False),
    )
