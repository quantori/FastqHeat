import hashlib
import logging
from pathlib import Path

from fastqheat.typing_helpers import PathType


def _count_lines(path: Path, chunk_size: int = 8 * 10**6) -> int:
    # NOTE: actually counts newline characters, like wc -l would
    count = 0
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            count += chunk.count(b'\n')

    return count


def get_info_about_all_loaded_lines(run_accession: str, path: PathType = ".") -> tuple[int, int]:
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

    fastq_files = list(Path(path).glob(f'{run_accession}*.fastq'))
    rate = None

    if not fastq_files:
        logging.error('The %s fastq file is empty or not exists', run_accession)
        exit(0)
    elif len(fastq_files) == 1:
        logging.debug('we loaded single-stranded read and have not to divide by 2 cnt of lines')
        rate = 1
    else:
        rate = 2

    total_lines = sum(map(_count_lines, fastq_files))
    logging.debug('All lines in all files of this run: %d', total_lines)
    return rate, total_lines


def get_cnt_of_coding_loaded_lines(run_accession: str, path: PathType = ".") -> int:
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

    return int(cnt)


def check_loaded_run(run_accession: str, path: PathType = ".", needed_lines_cnt: int = 1) -> bool:
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


def md5_checksum(path: PathType, md5: str) -> bool:
    """
    Compare mdh5 hash of file to md5 value retrieved
    from ENA file report
    Parameters
    ----------
    path: str
            path to the file
    md5: str
            md5 hash retrieved from ENA file report
    Returns
    -------
    bool
        True if mdh5 hash of file matches md5 value retrieved
        from ENA file report, othervise False
    """

    try:
        file = open(path, "rb")
    except FileNotFoundError:
        logging.warning('%s does not exist', path)
        return False

    md5_hash = hashlib.md5()
    chunk_size = md5_hash.block_size * 4_096

    with file as f:
        for byte_block in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(byte_block)

    return md5_hash.hexdigest() == md5
