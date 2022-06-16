import logging
import os

import requests
from check_result import check_loaded_run, md5_checksum
from get_sra_study_info import (
    download_metadata,
    get_full_metadata,
    get_run_uid_with_no_exception,
    get_run_uid_with_only_list,
    get_run_uid_with_skipped_list,
    get_run_uid_with_total_list,
    get_total_spots_with_only_list,
    get_webenv_and_query_key_with_skipped_list,
    get_webenv_and_query_key_with_total_list,
)


def handle_run(accession, accession_list, term, terms, method, out_dir, total_spots=1):
    """
    To download and check the quality of loading file

    Parameters
    ----------
    accession: str
    path: str
    total_spots: int

    Returns
    -------
        bool
    """
    try:
        if accession in accession_list:
            if method == 'f':
                if download_run_ftp(term=term, terms=terms, run=accession, out=out_dir):
                    logging.info('A try was finished.')
                    logging.info("Run {} was correctly downloaded".format(accession))
                    return True
                else:
                    logging.warning("Run {} was loaded incorrectly!".format(accession))
                    return False
            elif method == 'q':
                if download_run_fasterq_dump(
                    term=term,
                    terms=terms,
                    run=accession,
                    out=out_dir,
                    total_spots=float(total_spots),
                ):
                    logging.info('A try was finished.')
                    logging.info("Run {} was correctly downloaded".format(accession))
                    return True
                else:
                    logging.warning("Run {} was loaded incorrectly!".format(accession))
                    return False
            elif method == 'a':
                if download_run_aspc(term=term, terms=terms, run=accession, out=out_dir):
                    logging.info('A try was finished.')
                    logging.info("Run {} was correctly downloaded".format(accession))
                    return True
                else:
                    logging.warning("Run {} was loaded incorrectly!".format(accession))
                    return False
    except BaseException as e:
        logging.error(e)
        logging.debug("Accession {} not in the accession_list".format(accession))
        return True


def fastqheat(term, terms, show, only_list, skip_list, ff, value, out_dir, method, op):
    """
    This script help to download metagenomic data (in fastq/fastq.gz format) as well as metadata (in CSV/JSON/YAML format).

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
        -E, --explore         Explorer chooses between 2 options of what to do
                              with accession download metadata or run
                              itself from SRA/ENA. To download metadata
                              it should be followed with i, to download
                              runs- r.
        -F, --format          File format of downloaded metadata file.
                              3 options are available: CSV, JSON, YAML.
                              To download CSV choose c, JSON- j and YAML- y.
        -V, --value           Values for ENA report to retrieve metadata. By
                              default values are provided, but can be manually
                              entered too. Default values are: study_accession,
                              sample_accession,experiment_accession,read_count,base_count.
                              To write with '"," and without spaces.
        -N, --only            The only_list. The list of the certain items
                              to download.
                              To write with '"," and without spaces.
        -P, --skip            The skip_list. The list of the items to do not
                              download. To write with ',' and without spaces.
                              Warning: Skip parameter has the biggest priority.
                              If one run id has been pointed in skip_list and
                              in only_list, this run will be skipped.
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
    Ex 4: download all files using Aspera
                        python3 fastqheat.py SRP163674 -M a
    Ex 5: download metadata and format of file is CSV
                        python3 fastqheat.py SRP163674 -E i -F c
    Ex 6: download metadata, format of file is YAML and values are experiment_title, base_count
                        python3 fastqheat.py SRP163674 -E i -F c -V "experiment_title,base_count"
    Ex 7: download runs of multiple study accessions from .txt file using fasterq_dump
                        python3 fastqheat.py *.txt -M q


    """
    if len(terms) == 0:
        accession_list = []
        total_spots = []
        if show:
            if only_list == [] and skip_list == []:
                webenv, query_key = get_webenv_and_query_key_with_total_list(term)
                accession_list, total_spots = get_run_uid_with_no_exception(webenv, query_key)
            elif skip_list != []:
                webenv, query_key = get_webenv_and_query_key_with_skipped_list(
                    term=term, skip_list=skip_list
                )
                accession_list, total_spots = get_run_uid_with_no_exception(webenv, query_key)
            elif only_list != []:
                accession_list, total_spots = get_run_uid_with_only_list(only_list)
        else:
            if only_list == [] and skip_list == []:
                accession_list, total_spots = get_run_uid_with_total_list(term, method)
            elif skip_list != []:
                accession_list, total_spots = get_run_uid_with_skipped_list(term, skip_list, method)
            elif only_list != []:
                if method == 'q':
                    accession_list = only_list
                    total_spots = get_total_spots_with_only_list(only_list)
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
                        total_spots=total_spots[i],
                    )
                else:
                    success = handle_run(accession=accession_list[i], method=method)
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
                                total_spots=total_spots[i],
                            )
                        else:
                            handle_run(accession=accession_list[i], method=method)
                    else:
                        pass
            logging.info("All runs were loaded.")
        else:
            # This branch downloads metadata
            logging.info('Start getting metadata from ENA')
            metadata = get_full_metadata(accession_list, value)
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
                webenv, query_key = get_webenv_and_query_key_with_total_list(term=term)
                accession_list, total_spots = get_run_uid_with_no_exception(webenv, query_key)
            else:
                accession_list, total_spots = get_run_uid_with_total_list(term, method)
            # download every Run / metadata
            if op == "i":
                # This branch downloads metadata
                logging.info('Start getting metadata from ENA')
                metadata = get_full_metadata(accession_list, value)
                download_metadata(metadata, ff, term, out_dir)
                logging.info("Metadata has been loaded.")
            elif op == "r":
                # This branch downloads study runs
                for i in range(0, len(accession_list)):
                    if method == "q":
                        success = handle_run(
                            accession=accession_list[i],
                            method=method,
                            total_spots=total_spots[i],
                        )
                    else:
                        success = handle_run(accession=accession_list[i], method=method)
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
                                    total_spots=total_spots[i],
                                )
                            else:
                                handle_run(accession=accession_list[i], method=method)
                        else:
                            pass
                    logging.info(f"All runs were loaded from {term}.")


def download_run_fasterq_dump(term, terms, run, out, total_spots=1):
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
    if len(terms) != 0:
        download_bash_command = f"fasterq-dump {run} -O {out}/{term} -p"
        logging.debug(download_bash_command)
        logging.info('Try to download {} file'.format(run))
        os.system(download_bash_command)
        # check completeness of the file and return boolean
        return check_loaded_run(
            run_accession=run, path=f"{out}/{term}", needed_lines_cnt=total_spots
        )
    else:
        download_bash_command = f"fasterq-dump {run} -O {out} -p"
        logging.debug(download_bash_command)

        logging.info('Try to download {} file'.format(run))
        # execute command in commandline
        os.system(download_bash_command)
        # check completeness of the file and return boolean
        return check_loaded_run(run_accession=run, path=out, needed_lines_cnt=total_spots)


def download_run_ftp(term, terms, run, out):
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

    bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={run}&result=read_run&fields=fastq_ftp,fastq_md5&format=json"
    response = requests.get(bash_command)
    ftps = response.json()[0]['fastq_ftp'].split(';')
    md5s = response.json()[0]['fastq_md5'].split(';')
    correctness = []

    for i in range(0, len(ftps)):
        SRR = ftps[i].split('/')[-1]
        md5 = md5s[i]
        if len(terms) != 0:
            download_bash_command = (
                f"mkdir -p {out}/{term} && curl -L {ftps[i]} -o {out}/{term}/{SRR}"
            )
            logging.debug(download_bash_command)
            logging.info('Try to download {} file'.format(run))
            os.system(download_bash_command)
            # check completeness of the file and return boolean
            correctness.append(md5_checksum(SRR, f"{out}/{term}", md5))
        else:
            download_bash_command = f"curl -L {ftps[i]} -o {out}/{SRR}"
            logging.debug(download_bash_command)
            logging.info('Try to download {} file'.format(run))
            # execute command in commandline
            os.system(download_bash_command)
            # check completeness of the file and return boolean
            correctness.append(md5_checksum(SRR, out, md5))
    return all(correctness)


def download_run_aspc(term, terms, run, out):
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

    bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={run}&result=read_run&fields=fastq_aspera,fastq_md5&format=json"
    response = requests.get(bash_command)
    asperas = response.json()[0]['fastq_aspera'].split(';')
    md5s = response.json()[0]['fastq_md5'].split(';')
    correctness = []

    for i in range(0, len(asperas)):
        SRR = asperas[i].split('/')[-1]
        md5 = md5s[i]
        if len(terms) != 0:

            download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{asperas[i]} . && mkdir -p {out}/{term} && mv {SRR} {out}/{term}/{SRR}'

            logging.debug(download_bash_command)

            logging.info('Try to download {} file'.format(run))
            # execute command in commandline
            os.system(download_bash_command)
            # check completeness of the file and return boolean
            correctness.append(md5_checksum(SRR, f"{out}/{term}", md5))
        else:
            if out != '.':
                download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{asperas[i]} . && mv {SRR} {out}/{SRR}'
            else:
                download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{asperas[i]} .'

                logging.debug(download_bash_command)

                logging.info('Try to download {} file'.format(run))
                # execute command in commandline
                os.system(download_bash_command)
                # check completeness of the file and return boolean
                correctness.append(md5_checksum(SRR, out, md5))
    return all(correctness)
