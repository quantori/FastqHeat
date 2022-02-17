import logging
import os

import requests

from study_info.check_result import check_loaded_run, md5_checksum


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
                run_accession=run,
                path=f"{out}/{term}",
                needed_lines_cnt=total_spots
        )
    else:
        download_bash_command = f"fasterq-dump {run} -O {out} -p"
        logging.debug(download_bash_command)

        logging.info('Try to download {} file'.format(run))
        # execute command in commandline
        os.system(download_bash_command)
        # check completeness of the file and return boolean
        return check_loaded_run(
                        run_accession=run,
                        path=out,
                        needed_lines_cnt=total_spots
                )


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
            download_bash_command = f"mkdir -p {out}/{term} && curl -L {ftps[i]} -o {out}/{term}/{SRR}"
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
