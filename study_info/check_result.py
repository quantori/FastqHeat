import hashlib
import logging
import os


def get_info_about_all_loaded_lines(run_accession, path="."):
    """
    Count lines in real loaded file(s) and return it

    Parameters
    ----------
    run_accession: str
            Run's name (accession) like SRR...
    path: str
            path to the directory

    Returns
    -------
    """

    filename = "{}*.fastq".format(run_accession)
    filename = os.path.join(path, filename)

    wc = "wc -l {}".format(filename)
    entries = os.popen(wc).read()

    entries = entries.strip('\'').split('\n')[:-1]

    # get cnt entries
    cnt_entries = len(entries)

    rate = None
    if cnt_entries == 0:
        logging.error('The %s fastq file is empty or not exists', run_accession)
        exit(0)
    elif cnt_entries == 1:
        logging.debug('we loaded single-stranded read and have not to divide by 2 cnt of lines')
        rate = 1
    else:
        #  for two-stranded file the output will be:
        #  537692 SRR7969892_1.fastq\n  537692 SRR7969892_2.fastq\n  1075384 total
        rate = 2

    # get last entry and its value
    all_lines = entries[cnt_entries - 1].strip().split(' ')[0]
    logging.debug('All lines in all files of this run: %s', all_lines)

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

    rate, total = get_info_about_all_loaded_lines(run_accession=run_accession, path=path)

    # 4 - fixed because of a fastq file content
    cnt = (total / rate) / 4
    logging.debug('%d coding lines have been downloaded', cnt)

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

    cnt_loaded = get_cnt_of_coding_loaded_lines(run_accession=run_accession, path=path)

    if cnt_loaded == needed_lines_cnt:
        logging.info(
            'Current Run: %s with %d total spots has been successfully downloaded',
            run_accession,
            needed_lines_cnt,
        )
        return True
    else:
        logging.warning(
            'Loaded %s lines, but described %d lines. File has been downloaded INCORRECTLY',
            cnt_loaded,
            needed_lines_cnt,
        )
        return False


def md5_checksum(file, out, md5):
    """
    Compare mdh5 hash of file to md5 value retrieved
    from ENA file report

    Parameters
    ----------
    file: str
            Name of the downloaded Run Accession file
    out: str
            path to the directory
    md5: str
            md5 hash retrieved from ENA file report
    Returns
    -------
    bool
        True if mdh5 hash of file matches md5 value retrieved
        from ENA file report, othervise False
    """

    md5_hash = hashlib.md5()
    try:
        with open(f"{out}/{file}", "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                md5_hash.update(byte_block)
            return md5_hash.hexdigest() == md5
    except FileNotFoundError:
        logging.warning(f'{out}/{file} does not exist')
