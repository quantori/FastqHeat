import logging
import os
import requests

from study_info.check_result import check_loaded_run, md5_checksum


def download_run_fasterq_dump(run, out, total_spots=1):
    """
    Download the run from database using fasterq_dump and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """

    download_bash_command = "fasterq-dump " + run + " -O " + out + ' -p'
    logging.debug(download_bash_command)

    logging.info('Try to download {} file'.format(run))
    # execute command in commandline
    os.system(download_bash_command)
    return check_loaded_run(
                run_accession=run,
                path=out,
                needed_lines_cnt=total_spots
        )


def download_run_ftp(run, out):
    """
    Download the run from database using FTP and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """
    bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={run}&result=read_run&fields=fastq_ftp,fastq_md5&format=json"
    response = requests.get(bash_command)
    ftps = response.json()[0]['fastq_ftp'].split(';')
    md5s = response.json()[0]['fastq_md5'].split(';')
    correctness = []

    for i in range(0, len(ftps)):
        SRR = ftps[i].split('/')[-1]
        md5 = md5s[i]
        download_bash_command = "curl -L " + ftps[i] + " -o " + out + "/" + SRR
        logging.debug(download_bash_command)

        logging.info('Try to download {} file'.format(run))
        # execute command in commandline
        os.system(download_bash_command)
        correctness.append(md5_checksum(SRR, out, md5))
    return all(correctness)


def download_run_aspc(run, out):
    """
    Download the run from database using Aspera and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """
    bash_command = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={run}&result=read_run&fields=fastq_aspera,fastq_md5&format=json"
    response = requests.get(bash_command)
    asperas = response.json()[0]['fastq_aspera'].split(';')
    md5s = response.json()[0]['fastq_md5'].split(';')
    correctness = []

    for i in range(0, len(asperas)):
        SRR = asperas[i].split('/')[-1]
        md5 = md5s[i]
        if out != '.':
            download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{asperas[i]} . && mv {SRR} {out}/{SRR}'
        else:
            download_bash_command = f'ascp -QT -l 300m -P33001 -i $HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh era-fasp@{asperas[i]} .'

        logging.debug(download_bash_command)

        logging.info('Try to download {} file'.format(run))
        # execute command in commandline
        os.system(download_bash_command)
        correctness.append(md5_checksum(SRR, out, md5))
    return all(correctness)
