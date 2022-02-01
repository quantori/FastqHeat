import logging
import argparse
import os
import urllib3
import ssl
import requests

from download import download_run_ftp, download_run_fasterq_dump, download_run_aspc

from study_info.get_sra_study_info import get_webenv_and_query_key_with_skipped_list, get_webenv_and_query_key_with_total_list, get_run_uid_with_no_exception, get_run_uid_with_skipped_list, get_run_uid_with_total_list, get_run_uid_with_only_list, get_metadata, download_metadata


def handle_run(accession, method, total_spots=1):
    """
    To download and check the quality of loading file

    Parameters
    ----------
    path: str
    accession: str
    total_spots: object

    Returns
    -------

    """
    try:
        if accession in accession_list:
            if method == 'f':
                if(download_run_ftp(term=term, terms=terms,
                                    run=accession, out=out_dir)):
                    logging.info('A try was finished.')
                    logging.info("Run {} was correctly downloaded".format(
                        accession))
                    return True
                else:
                    logging.warning("Run {} was loaded incorrectly!".format(
                        accession))
                    return False
            elif method == 'q':
                # download_run_fasterq_dump(run=accession, out=out_dir)
                # return True
                if(download_run_fasterq_dump(term=term, terms=terms,
                                             run=accession, out=out_dir,
                                             total_spots=float(total_spots))):
                    logging.info('A try was finished.')
                    logging.info("Run {} was correctly downloaded".format(
                        accession))
                    return True
                else:
                    logging.warning("Run {} was loaded incorrectly!".format(
                        accession))
                    return False
            elif method == 'a':
                if(download_run_aspc(term=term, terms=terms,
                                     run=accession, out=out_dir)):
                    logging.info('A try was finished.')
                    logging.info("Run {} was correctly downloaded".format(
                        accession))
                    return True
                else:
                    logging.warning("Run {} was loaded incorrectly!".format(
                        accession))
                    return False
    except:
        logging.debug("Accession {} not in the accession_list".format(
                accession))
        return True


if __name__ == "__main__":
    """
    This script help to download metagenomic data (in fastq format).
        
    How it works.
   
        Parameters:
    
    positional arguments:
            term              The name of SRA Study identifier, looks like SRP... or ERP... or DRP...

    optional arguments:
        -h, --help            show this help message and exit
        -L, --log             To point logging level (debug, info, warning, error. "info" by default)
        -M, --method          Method of downloading fastq or fastq.gz file. There are 3 options for downloading data: FTP, Aspera and
                              fasterq_dump. To use Aspera specify after -M command a, to use FTP specify f, and for fasterq_dump specify q.
        -N, --only            The only_list. The list of the certain items to download.
                              To write with '"," and without spaces.
        -P, --skip            The skip_list. The list of the items to do not download. To write with ',' and without spaces.
                              Warning: Skip parameter has the biggest priority.
                              If one run id has been pointed in skip_list and in only_list, this run will be skipped.
        -O, --out             Output directory
        -S, --show            show lxml file with all Run data (yes/no)
    
    Template of query:
            fastqheat.py {SRA Study identifier name SRP...} --skip_list {run id SRR...} --show yes 
            
            fastqheat.py {SRA Study identifier name SRP...} --only_list {run id SRR...} 
   
    Ex 1: download all into the directory
                        python3 fastqheat.py SRP163674 --out /home/user/tmp
    Ex 2: download all files except some pointed items.
                        python3 fastqheat.py SRP163674 -P "SRR7969889,SRR7969890,SRR7969890"
    Ex 3: download only pointed items and show the details of the loading process.
                        python3 fastqheat.py SRP163674 -N "SRR7969891,SRR7969892" --show yes
    
        
    """
    # For debugging use
    # term = 'SRP150545'  #   6 files more than 2-3Gb each
    # term = 'SRP163674'  # 129 files, 2-8 Mb each (ex of double stranded SRR7969890)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "term",
        help="The name of SRA Study identifier, looks like SRP... or ERP... or DRP...  or .txt file name which includes multiple SRA Study identifiers",
        action="store"
    )
    parser.add_argument(
        "-L", "--log",
        help="To point logging level (debug, info, warning, error.",
        action="store",
        default="info"
    )
    parser.add_argument(
        "-N", "--only",
        help="The only_list. The list of the certain items to download. To write with ',' and without spaces.",
        action="store"
    )
    parser.add_argument(
        "-O", "--out",
        help="Output directory",
        action="store",
        default="."
    )
    parser.add_argument(
        "-M", "--method",
        help="Choose different type of methods that should be used for data retrieval: Aspera (a), FTP (f), fasterq_dump (q). By default it is fasterq_dump (q)",
        action="store",
        default='q'
    )
    parser.add_argument(
        "-P", "--skip",
        help="The skip_list. The list of the items to do not download. To write with ',' and without spaces. \
        Warning: Skip parameter has the biggest priority.\
        If one run id has been pointed in skip_list and in only_list, this run will be skipped.",
        action="store"
    )
    parser.add_argument(
        "-E", "--explore",
        help="Choose between 2 options:download runs or download metadata. Argument should be followed with \
        i for Metadata and r for Runs.\
        By default it will always be set to r to retrieve runs.",
        action="store",
        default="r"
    )
    parser.add_argument(
        "-F", "--format",
        help="Choose which format to use to download metadata:CSV, JSON on YAML. \
        c for CSV, j for JSON and y for YAML.\
        By default it will always be set to j.",
        action="store",
        default="j"
    )
    parser.add_argument(
        "-V", "--value",
        help="Choose column selection from ENA. To write with ',' and without spaces. \
        By default it will always be set to this list:\
        study_accession,sample_accession,experiment_accession,read_count,base_count.",
        action="store",
        default="study_accession,sample_accession,experiment_accession,read_count,base_count"
    )
    parser.add_argument(
        "-S", "--show",
        help="To show lxml file in a terminal with all Run data (yes/no).",
        action="store",
        default="no"
    )

    args = parser.parse_args()

    # choose method type
    if args.method:
        method = args.method
    else:
        logging.error('Choose any method for data retrieval')
        exit(0)

    # choose what to download metadata or runs
    if args.explore:
        op = args.explore
    else:
        logging.error('Choose option for data retrieval')
        exit(0)

    # choose file format of downloaded metadata
    if op == "i":
        if args.format:
            ff = args.format
        else:
            logging.error('Choose option for metadata format')
            exit(0)

    # choose values for parameters for metadata
    if op == "i":
        if args.value:
            value = args.value
        else:
            logging.error('Choose correct values for metadata')
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
    parser.add_argument('--version',
                        action='version',
                        version=f'{tool} which use {fd_version} version'
                        )

    # args for skipping Runs
    if args.skip:
        skip_list = args.skip
        skip_list = skip_list.split(',')
    else:
        skip_list = []

    # args for list of needed Runs
    if args.only:
        only_list = args.only
        only_list = only_list.split(',')
        logging.debug(only_list)
    else:
        only_list = []

    # args for show lxml file of Run description
    if args.show:
        show = args.show
        if show == 'yes':
            show = True
        else:
            show = False
    else:
        show = False

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
        logging.basicConfig(
            level=LOGGING_LEVEL,
            format='[level=%(levelname)s]: %(message)s'
        )

        # Get webenv and query_key from eSearch results to use for eFetch
        # Use this functions only when show tree is true and there is
        # skipped list or total list provided from single SRP
        # The list of names of runs will be different depending on whether
        # or not user wants to see lxml tree and whether or not
        # all runs should be dowloaded from SRP or only specific list
        # should be downloaded or specific list should be skipped
        if len(terms) == 0:
            accession_list = []
            total_spots = []
            if show:
                if only_list == [] and skip_list == []:
                    webenv, query_key = get_webenv_and_query_key_with_total_list(
                        term)
                    accession_list, total_spots = get_run_uid_with_no_exception(
                        webenv, query_key
                    )
                elif skip_list != []:
                    webenv, query_key = get_webenv_and_query_key_with_skipped_list(
                        term=term, skip_list=skip_list
                    )
                    accession_list, total_spots = get_run_uid_with_no_exception(
                        webenv, query_key
                    )
                elif only_list != []:
                    accession_list, total_spots = get_run_uid_with_only_list(
                                                    only_list)
            else:
                if only_list == [] and skip_list == []:
                    accession_list, total_spots = get_run_uid_with_total_list(term, method)
                elif skip_list != []:
                    accession_list, total_spots = get_run_uid_with_skipped_list(
                                                    term, skip_list, method)
                elif only_list != []:
                    if method == 'q':
                        accession_list = only_list
                        for i in only_list:
                            url = f'https://www.ebi.ac.uk/ena/portal/api/filereport?accession={i}&result=read_run&fields=run_accession,read_count&format=json'
                            response = requests.get(url)
                            total_spots.append(response.json()[0]['read_count'])
                    else:
                        accession_list = only_list
            if op == "r":
                # This branch downloads only study runs
                # Download every Run
                for i in range(0, len(accession_list)):
                    if method == "q":
                        success = handle_run(
                                accession=accession_list[i],
                                method=method,
                                total_spots=total_spots[i]
                        )
                    else:
                        success = handle_run(
                                accession=accession_list[i],
                                method=method
                        )
                    if success:
                        pass
                    else:
                        logging.warning("Do you want to reload it one more time? (y/n)")
                        answer = input()
                        if answer == "y":
                            if method == "q":
                                handle_run(
                                        accession=accession_list[i],
                                        method=method,
                                        total_spots=total_spots[i]
                                )
                            else:
                                handle_run(
                                        accession=accession_list[i],
                                        method=method
                                )
                        else:
                            pass
                logging.info("All runs were loaded.")
            else:
                # This branch downloads metadata
                logging.info('Start getting metadata from ENA')
                if show:
                    metadata = []
                    for accession in accession_list:
                        metadata.extend(get_metadata(term=accession,
                                                     value=value))
                else:
                    if only_list == [] and skip_list == []:
                        metadata = get_metadata(term=term, value=value)
                    else:
                        metadata = []
                        for accession in accession_list:
                            metadata.extend(get_metadata(term=accession,
                                                         value=value))
                logging.info('Start download metadata retrieved from ENA')
                download_metadata(metadata, ff, term, out_dir)
                logging.info("Metadata has been loaded.")
        else:
            # This branch downloads data using .txt file with multiple study accession
            accession_list = []
            total_spots = []
            for term in terms:
                logging.info(f"Start working on Study Accession {term}")
                if show:
                    webenv, query_key = get_webenv_and_query_key_with_total_list(
                            term=term)
                    accession_list, total_spots = get_run_uid_with_no_exception(
                            webenv, query_key
                        )
                else:
                    accession_list, total_spots = get_run_uid_with_total_list(term, method)
                # download every Run / metadata
                metadata = []
                for i in range(0, len(accession_list)):
                    if op == "r":
                        # This branch downloads study runs
                        if method == "q":
                            success = handle_run(
                                    accession=accession_list[i],
                                    method=method,
                                    total_spots=total_spots[i]
                            )
                        else:
                            success = handle_run(
                                    accession=accession_list[i],
                                    method=method
                            )
                        if success:
                            pass
                        else:
                            logging.warning("Do you want to reload it one more time? (y/n)")
                            answer = input()
                            if answer == "y":
                                if method == "q":
                                    handle_run(
                                            accession=accession_list[i],
                                            method=method,
                                            total_spots=total_spots[i]
                                    )
                                else:
                                    handle_run(
                                            accession=accession_list[i],
                                            method=method
                                    )
                            else:
                                pass
                        logging.info(f"All runs were loaded from {term}.")
                    else:
                        # This branch retrieves metadata
                        metadata.extend(get_metadata(term=accession_list[i],
                                                     value=value))
                else:
                    if op == "i":
                        download_metadata(metadata, ff, term, out_dir)
                        logging.info("Metadata has been loaded.")
                        metadata = []
    except ValueError as e:
        logging.error(e)
        print("Unexpected exit")
        exit(0)
    except (requests.exceptions.SSLError,
            urllib3.exceptions.MaxRetryError,
            ssl.SSLEOFError) as e:
        logging.error(e)
        print("Too many requests were made. Exiting system.")
        exit(0)
    except KeyboardInterrupt:
        print("Session was interrupted!")
        exit(0)
