import logging
import argparse
import os

from download import download_run_ftp, download_run_fasterq_dump, download_run_aspc
from manage_lists.filter_list import remove_skipped_idx, get_only_idx
from study_info.check_result import check_loaded_run

from study_info.get_sra_study_info import get_retmax, get_id_list, get_run_uid_by_id


def handle_run(accession,
               total_spots,
               path, method):
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

    if accession in accession_list:
        if method == 'f':
            download_run_ftp(run=accession, out=out_dir)
        elif method == 'q':
            download_run_fasterq_dump(run=accession, out=out_dir)
        elif method == 'a':
            download_run_aspc(run=accession, out=out_dir)

        if check_loaded_run(
                run_accession=accession,
                path=path,
                needed_lines_cnt=total_spots
        ):
            logging.info("Run {} was correctly downloaded".format(accession))
            return True
        else:
            logging.warning("Run {} was loaded incorrectly!".format(accession))
            return False
    else:
        logging.debug("Accession {} not in the accession_list".format(accession))
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
        help="The name of SRA Study identifier, looks like SRP... or ERP... or DRP...",
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

    try:
        fd_version = ''
        if method == 'q':
            fd_version = os.popen("fasterq-dump --version").read()
        elif method == 'a':
            fd_version = os.popen("aspera --version").read()
    except IOError as e:
        logging.error(e)
        logging.error("SRA Toolkit not installed or not pointed in path")
        exit(0)
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0 which use {} version'.format(fd_version))

    if args.term:
        term = args.term
    else:
        logging.error('Use correct term name')
        exit(0)

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

        # Get count of runs in experiment
        cnt = get_retmax(term=term)

        # Get the list of all identifiers of all runs of SRA study
        idx = get_id_list(
            term=term,
            retmax=cnt
        )

        # The dictionary where stored pair accession_name:total_spot.
        # Where accession name is a name of the run and looking like SRR...
        # and total spots is the count of lines in the file.
        # Accession name will be a key, total spots will be a value
        runs = {}

        # The list of names of runs which will be loaded
        accession_list = []

        # Get run parameters:
        # - dict of Run's name (accessions)
        # - cnt of lines in an each accession
        for i, identifier in enumerate(idx):

            # get all Run's attributes
            run = get_run_uid_by_id(
                id=identifier,
                show=show
            )
            # Take the RUN name looking like SRR... - run accession
            accession = run['accession']

            try:
                # take and convert the count of lines in the run file
                total_spots = int(run['total_spots'])
                # ... and put pair {run_name:cnt of lines} into the dictionary
                runs[accession] = total_spots

                # add this accession into the FULL list of names
                accession_list.append(accession)
            except TypeError:
                logging.error('Incorrect attribute name in Run description (lxml response)')
                exit(0)

            # TODO use for tests only
            # if i == 12:
            #     break

        # Remove runs from the "skip list"
        accession_list = remove_skipped_idx(
            total_list=accession_list,
            skip_list=skip_list
        )

        # Get idx from the "only list"
        accession_list = get_only_idx(
            total_list=accession_list,
            only_list=only_list
        )

        # download every Run
        for accession, total_spots in runs.items():
            success = handle_run(
                    accession=accession,
                    total_spots=total_spots,
                    path=out_dir,
                    method=method
            )

            if success:
                pass
            else:
                logging.warning("Do you want to reload it one more time? (y/n)")
                answer = input()
                if answer == "y":
                    handle_run(
                        accession=accession,
                        total_spots=total_spots,
                        path=out_dir,
                        method=method
                    )
                else:
                    pass
        print("All runs was loaded.")
    except ValueError as e:
        logging.error(e)
        print("Unexpected exit")
        exit(0)
