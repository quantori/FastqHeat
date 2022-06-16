import argparse
import logging
import os
import re
import ssl

import requests
import urllib3

from download import download_run_aspc, download_run_fasterq_dump, download_run_ftp
from study_info.get_sra_study_info import get_run_uid


def handle_methods(term, method, out):
    SRR_pattern = re.compile(r'^(SRR|ERR|DRR)\d+$')
    SRP_pattern = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')
    if method == "f":
        if SRR_pattern.search(term) is not None:
            accession = term
            success = download_run_ftp(accession, term, out)
            if success:
                pass
            else:
                logging.warning(f"Failed to download {accession}. Trying once more.")
                success = download_run_ftp(accession, term, out)
                if success:
                    logging.info("The second try was successful!")
                    pass
                else:
                    logging.error(f"Failed the second try. Skipping the {accession}")
                    pass
        elif SRP_pattern.search(term) is not None:
            accession_list, total_spots = get_run_uid(term)
            for i in range(0, len(accession_list)):
                accession = accession_list[i]
                success = download_run_ftp(accession, term, out)

                if success:
                    pass
                else:
                    logging.warning(f"Failed to download {accession}. Trying once more.")
                    success = download_run_ftp(accession, term, out)
                    if success:
                        logging.info("The second try was successful!")
                        pass
                    else:
                        logging.error(f"Failed the second try. Skipping the {accession}")
                        pass

    if method == "a":
        if SRR_pattern.search(term) is not None:
            accession = term
            success = download_run_aspc(accession, term, out)

            if success:
                pass
            else:
                logging.warning(f"Failed to download {accession}. Trying once more.")
                success = download_run_aspc(accession, term, out)
                if success:
                    logging.info("The second try was successful!")
                    pass
                else:
                    logging.error(f"Failed the second try. Skipping the {accession}")
                    pass
        if SRP_pattern.search(term) is not None:
            accession_list, total_spots = get_run_uid(term)
            for i in range(0, len(accession_list)):
                accession = accession_list[i]
                success = download_run_aspc(accession, term, out)

                if success:
                    pass
                else:
                    logging.warning(f"Failed to download {accession}. Trying once more.")
                    success = download_run_aspc(accession, term, out)
                    if success:
                        logging.info("The second try was successful!")
                        pass
                    else:
                        logging.error(f"Failed the second try. Skipping the {accession}")
                        pass

    if method == "q":
        if SRR_pattern.search(term) is not None:
            accession = term
            bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields=read_count&format=json"
            response = requests.get(bash_command)
            total_spots = int(response.json()[0]['read_count'])
            success = download_run_fasterq_dump(accession, term, total_spots, out)

            if success:
                pass
            else:
                logging.warning(f"Failed to download {accession}. Trying once more.")
                success = download_run_fasterq_dump(accession, term, total_spots, out)
                if success:
                    logging.info("The second try was successful!")
                    pass
                else:
                    logging.error(f"Failed the second try. Skipping the {accession}")
                    pass

        if SRP_pattern.search(term) is not None:
            accession_list, total_spots = get_run_uid(term)
            for i in range(0, len(accession_list)):
                accession = accession_list[i]
                read_count = total_spots[i]
                success = download_run_fasterq_dump(accession, term, read_count, out)

                if success:
                    pass
                else:
                    logging.warning(f"Failed to download {accession}. Trying once more.")
                    success = download_run_fasterq_dump(accession, term, read_count, out)
                    if success:
                        logging.info("The second try was successful!")
                        pass
                    else:
                        logging.error(f"Failed the second try. Skipping the {accession}")
                        pass


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
        action="store",
    )
    parser.add_argument(
        "-L",
        "--log",
        help="To point logging level (debug, info, warning, error.",
        action="store",
        default="info",
    )
    # parser.add_argument(
    #     "-N", "--only",
    #     help="The only_list. The list of the certain items to download. To write with ',' and without spaces.",
    #     action="store"
    # )
    parser.add_argument("-O", "--out", help="Output directory", action="store", default=".")
    parser.add_argument(
        "-M",
        "--method",
        help="Choose different type of methods that should be used for data retrieval: Aspera (a), FTP (f), fasterq_dump (q). By default it is fasterq_dump (q)",
        action="store",
        default='q',
    )
    # parser.add_argument(
    #     "-P", "--skip",
    #     help="The skip_list. The list of the items to do not download. \
    #     To write with ',' and without spaces. Warning: Skip parameter\
    #     has the biggest priority.\
    #     If one run id has been pointed in skip_list and in only_list, \
    #     this run will be skipped.",
    #     action="store"
    # )
    # parser.add_argument(
    #     "-E", "--explore",
    #     help="2 options:download runs or download metadata. \
    #     Argument should be followed with i for Metadata and r for Runs.\
    #     By default it will always be set to r to retrieve runs.",
    #     action="store",
    #     default="r"
    # )
    # parser.add_argument(
    #     "-F", "--format",
    #     help="File format of downloaded metadata:CSV, JSON on YAML. \
    #     c for CSV, j for JSON and y for YAML.\
    #     By default it will always be set to j.",
    #     action="store",
    #     default="j"
    # )
    # parser.add_argument(
    #     "-V", "--value",
    #     help="Column selection from ENA. To write with ',' and without spaces. \
    #     By default it will always be set to this list:\
    #     study_accession,sample_accession,experiment_accession,read_count,base_count",
    #     action="store",
    #     default="study_accession,sample_accession,experiment_accession,read_count,base_count"
    # )
    # parser.add_argument(
    #     "-S", "--show",
    #     help="To show lxml file in a terminal with all Run data (yes/no).",
    #     action="store",
    #     default="no"
    # )

    args = parser.parse_args()

    # choose method type
    if args.method:
        method = args.method
    else:
        logging.error('Choose any method for data retrieval')
        exit(0)

    # # choose what to download metadata or runs
    # if args.explore:
    #     op = args.explore
    # else:
    #     logging.error('Choose option for data retrieval')
    #     exit(0)

    # # choose file format of retrieved metadata
    # if op == "i":
    #     if args.format:
    #         ff = args.format
    #     else:
    #         logging.error('Choose option for metadata format')
    #         exit(0)

    # # choose values for parameters for metadata
    # if op == "i":
    #     if args.value:
    #         value = args.value
    #     else:
    #         logging.error('Choose correct values for metadata')
    #         exit(0)

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

    # # args for skipping Runs
    # if args.skip:
    #     skip_list = args.skip
    #     skip_list = skip_list.split(',')
    # else:
    #     skip_list = []

    # # args for list of needed Runs
    # if args.only:
    #     only_list = args.only
    #     only_list = only_list.split(',')
    #     logging.debug(only_list)
    # else:
    #     only_list = []

    # # args for show lxml file of Run description
    # if args.show:
    #     show = args.show
    #     if show == 'yes':
    #         show = True
    #     else:
    #         show = False
    # else:
    #     show = False

    out_dir = "."
    if args.out:
        if os.path.isdir(args.out):
            out_dir = args.out
        else:
            logging.error('Pointed directory does not exist.')
            exit(0)

    if args.term:
        term = args.term
        terms = []
        if term.endswith('.txt'):
            with open(f"{out_dir}/{term}", "r") as f:
                lines = f.readlines()
                terms = [line.strip() for line in lines]
        elif '.' not in term:
            pass
        else:
            logging.error('Use either correct term or only .txt file format.')
            exit(0)
    else:
        logging.error('Use correct term name.')
        exit(0)

    LOGGING_LEVEL = logging.INFO  # log level by default
    if args.log:
        log = args.log
        if log == 'info':
            LOGGING_LEVEL = logging.INFO
        if log == 'debug':
            LOGGING_LEVEL = logging.DEBUG
        if log == 'warning':
            LOGGING_LEVEL = logging.WARNING
        if log == 'error':
            LOGGING_LEVEL = logging.ERROR

    try:
        logging.basicConfig(level=LOGGING_LEVEL, format='[level=%(levelname)s]: %(message)s')

        if len(terms) == 0:
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
