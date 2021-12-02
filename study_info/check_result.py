import logging
import os
import glob


def get_info_about_all_loaded_lines(run_accession, path="."):
    """
    Count lines in real loaded file(s) and return it

    run_accession: str
            Run's name (accession) like SRR...
    path: str
            path to the directory

    Returns
    -------

    """
    all_lines = 0
    cnt_entries = 0
    m = [name for name in glob.glob(f'{path}/{run_accession}*.fastq.gz')]

    if len(m) == 0:
        filename = "{}*.fastq".format(run_accession)
        filename = os.path.join(path, filename)
        wc = "wc -l {}".format(filename)
        entries = os.popen(wc).read()
        entries = entries.strip('\'').split('\n')[:-1]
        # get cnt entries
        cnt_entries = len(entries)
        # get last entry and its value
        all_lines = entries[cnt_entries - 1].strip().split(' ')[0]
    else:
        filename = "{}*.fastq.gz".format(run_accession)
        filename = os.path.join(path, filename)
        wc = 'zcat {} | wc -l'.format(filename)
        entries = os.popen(wc).read()
        # get last entry and its value
        all_lines = int(entries)
        # get cnt entries
        wc1 = 'ls {} | wc -l'.format(filename)
        entries1 = os.popen(wc1).read()
        cnt_entries = int(entries1)

    rate = None
    if cnt_entries == 0:
        logging.error('The {} fastq file is empty or not exists'.format(run_accession))
        exit(0)
    elif cnt_entries == 1:
        logging.debug('we loaded single-stranded read and have not to divide by 2 cnt of lines')
        rate = 1
    else:
        #  for two-stranded file the output will be:
        #  537692 SRR7969892_1.fastq\n  537692 SRR7969892_2.fastq\n  1075384 total
        rate = 2

    logging.debug('All lines in all files of this run: {}'.format(all_lines))

    return rate, int(all_lines)


def get_cnt_of_coding_loaded_lines(run_accession, path="."):
    """
    Get cnt lines in loaded Run files

    Parameters
    ----------
    path: str
                path to the directory with fastq files
    run_accession: str
                Run's name (accession) like SRR...

    Returns
    -------
        int
    """

    rate, total = get_info_about_all_loaded_lines(
        run_accession=run_accession,
        path=path
    )

    # 4 - fixed because of a fastq file content
    cnt = (total / rate) / 4
    logging.debug('{} coding lines have been downloaded'.format(cnt))

    return cnt


def check_loaded_run(run_accession, path=".", needed_lines_cnt=1):
    """
    Check loaded run by lines in file cnt

    Parameters
    ----------
    path: str
    run_accession: str
                Run's name (accession) like SRR...
    needed_lines_cnt: int
                cnt lines in loaded file according to the SRA database entry

    Returns
    -------
        bool
    """

    cnt_loaded = get_cnt_of_coding_loaded_lines(
        run_accession=run_accession,
        path=path
    )

    if cnt_loaded == needed_lines_cnt:
        logging.info('Current Run: {} with {} total spots has been successfully downloaded'.format(
            run_accession,
            needed_lines_cnt
        ))
        return True
    else:
        logging.warning('Loaded {} lines, but described {} lines. File has been downloaded INCORRECTLY'.format(
            cnt_loaded,
            needed_lines_cnt
        ))
        return False
