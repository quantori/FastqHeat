import logging
import os


def download_run(run, out):
    """
    Download the run from database and check its params

    Parameters
    ----------
    run: str
            Run's name like SRR...
    out: str
            The output directory
    """

    download_bash_command = "fastq-dump --defline-seq '@$sn[_$rn]/$ri' --defline-qual '+' --split-files " + run + " --outdir " + out
    logging.debug(download_bash_command)

    logging.info('Try to download {} file'.format(run))
    # execute command in commandline
    os.system(download_bash_command)
    logging.info('A try was finished.')
