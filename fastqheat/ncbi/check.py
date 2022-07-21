import logging
import subprocess
from functools import partial
from pathlib import Path

from fastqheat import typing_helpers as th
from fastqheat.ena.ena_api_client import ENAClient

logger = logging.getLogger("fastqheap.ncbi.check")


def check(
    *,
    accessions: list[str],
    directory: th.PathType,
    attempts: int,
    attempts_interval: int,
    core_count: int,
) -> bool:
    """Check accessions in bulk."""
    check_func = partial(
        check_accession,
        attempts=attempts,
        attempts_interval=attempts_interval,
        core_count=core_count,
        internal_check=False,
    )
    directory = Path(directory)
    return all(check_func(accession, directory) for accession in accessions)


def check_accession(
    accession: str,
    path: Path,
    attempts: int = 1,
    attempts_interval: int = 1,
    core_count: int = 6,
    internal_check: bool = True,
) -> bool:
    """Check loaded run by lines in file cnt"""

    cnt_loaded = _get_cnt_of_coding_loaded_lines(
        accession=accession, path=path, core_count=core_count, internal_check=internal_check,
    )

    needed_lines_cnt = ENAClient(
        attempts=attempts, attempts_interval=attempts_interval
    ).get_read_count(accession)

    if cnt_loaded == needed_lines_cnt:
        logger.info(
            'Current Run: %s with %d total spots has been successfully downloaded',
            accession,
            needed_lines_cnt,
        )
        return True
    else:
        logger.warning(
            'Loaded %d lines, but described %d lines. File has been downloaded INCORRECTLY',
            cnt_loaded,
            needed_lines_cnt,
        )
        return False


def _count_lines(path: Path, chunk_size: int = 8 * 10**6) -> int:
    # NOTE: actually counts newline characters, like wc -l would
    count = 0
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            count += chunk.count(b'\n')

    return count


def _get_cnt_of_coding_loaded_lines(
    accession: str, core_count: int, path: Path, internal_check: bool,
) -> int:
    """Count lines in real loaded file(s) and return it."""

    with FilesToCheck(accession=accession, path=path, core_count=core_count, internal_check=internal_check) as fastq_files:

        if len(fastq_files) == 1:
            logger.debug('we loaded single-stranded read and have not to divide by 2 cnt of lines')
            rate = 1
        else:
            rate = 2

        total_lines = sum(map(_count_lines, fastq_files))
        logger.debug('All lines in all files of this run: %d', total_lines)

    # 4 - fixed because of a fastq file content
    cnt = (total_lines / rate) / 4
    logger.debug('%d coding lines have been downloaded', cnt)

    logger.debug('Removing unzipped temporary files...')

    return int(cnt)


class FilesToCheck:

    def __init__(self, accession: str, path: Path, core_count: int, internal_check: bool):
        self.accession = accession
        self.path = path
        self.core_count = core_count
        self.internal_check = internal_check

    def __enter__(self):
        if not self.path.match(self.accession):
            self.path = Path(self.path) / self.accession

        if self.internal_check:
            return list(self.path.glob(f'{self.accession}*.fastq'))

        fastq_files = list(self.path.glob(f'{self.accession}*.fastq.gz'))
        self._unzip(file_paths=fastq_files)

        if not fastq_files:
            raise ValueError("No files found")

        return fastq_files

    def __exit__(self, *args, **kwargs):
        if not self.internal_check:
            fastq_files = list(self.path.glob(f'{self.accession}*.fastq'))
            # remove temporary unzipped files
            [file.unlink() for file in fastq_files]

    def _unzip(self, file_paths: list[th.PathType]):
        """Unzip files."""
        if not file_paths:
            raise ValueError("No files have been given to unpigz")
        logger.debug("Unzipping %s...", "; ".join([str(file) for file in file_paths]))
        subprocess.run(['unpigz', '--keep', '--processes', str(self.core_count), *file_paths],
                       check=True)