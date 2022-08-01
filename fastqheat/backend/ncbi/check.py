import logging
import subprocess
import typing as tp
from pathlib import Path

from fastqheat import typing_helpers as th
from fastqheat.backend.common import BaseAccessionChecker
from fastqheat.exceptions import ValidationError

logger = logging.getLogger("fastqheap.ncbi.check")


def check(
    *,
    accessions: list[str],
    directory: th.PathType,
    attempts: int,
    attempts_interval: int,
    core_count: int,
    zipped: bool = True,
) -> None:
    """Check accessions in bulk."""

    access_checker = AccessionChecker(
        directory=Path(directory),
        attempts=attempts,
        attempts_interval=attempts_interval,
        core_count=core_count,
        zipped=zipped,
    )

    successfully_checked = access_checker.check_accessions(accessions)
    logger.info("%d/%d files were checked successfully.", successfully_checked, len(accessions))


class AccessionChecker(BaseAccessionChecker):
    def __init__(
        self, directory: Path, attempts: int, attempts_interval: int, core_count: int, zipped: bool
    ) -> None:
        super().__init__(directory, attempts, attempts_interval)
        self.core_count = core_count
        self.zipped = zipped

    def check_accession(self, accession: str) -> bool:
        """Check loaded run by lines in file cnt"""
        logger.debug("Checking accession %s", accession)

        cnt_loaded = self._get_cnt_of_coding_loaded_lines(accession=accession)
        needed_lines_cnt = self.ena_client.get_read_count(accession)

        if cnt_loaded != needed_lines_cnt:
            raise ValidationError(
                f"Loaded {cnt_loaded} lines, but described {needed_lines_cnt} lines."
                f"File has been downloaded INCORRECTLY"
            )

        logger.info(
            'Current Run: %s with %d total spots has been successfully downloaded',
            accession,
            needed_lines_cnt,
        )
        return True

    @staticmethod
    def _count_lines(path: Path, chunk_size: int = 8 * 10**6) -> int:
        # NOTE: actually counts newline characters, like wc -l would
        count = 0
        with path.open('rb') as file:
            for chunk in iter(lambda: file.read(chunk_size), b''):
                count += chunk.count(b'\n')

        return count

    def _get_cnt_of_coding_loaded_lines(
        self,
        accession: str,
    ) -> int:
        """Count lines in real loaded file(s) and return it."""

        with FileManager(
            accession=accession, path=self.directory, core_count=self.core_count, zipped=self.zipped
        ) as fastq_files:

            if len(fastq_files) == 1:
                logger.debug(
                    'we loaded single-stranded read and have not to divide by 2 cnt of lines'
                )
                rate = 1
            else:
                rate = 2

            total_lines = sum(map(self._count_lines, fastq_files))
            logger.debug('All lines in all files of this run: %d', total_lines)

        # 4 - fixed because of a fastq file content
        cnt = (total_lines / rate) / 4
        logger.debug('%d coding lines have been downloaded', cnt)

        return int(cnt)


class FileManager:
    """
    Returns paths to files that should be checked

    Should be used like:

    with FilesToCheck(accession, path, core_count, zipped) as fastq_files:
        # do_something with files

    It will return paths to unzipped fastq files, matched by given accession in their name
    If files are archived (have *.gz extension), they will be unzipped. Then, on exit, unzipped
    files will be removed.

    accession - accession name
    path - path to folder that have folders name like accessions inside

    /some/output/directory/ <- this is the path argument
    └── SRR7882015
        ├── SRR7882015_1.fastq.gz
        └── SRR7882015_2.fastq.gz

    core_count - how much cpu cores should pigz and unpigz use
    zipped - bool flag; basically says if we should expect the files in path to be zipped
    or unzipped
    """

    def __init__(self, accession: str, path: Path, core_count: int, zipped: bool):
        self.accession = accession
        self.path = path
        self.core_count = core_count
        self.zipped = zipped

    def __enter__(self) -> list[Path]:
        if not self.path.match(self.accession):
            self.path = Path(self.path) / self.accession

        if not self.zipped:
            return list(self.path.glob(f'{self.accession}*.fastq'))

        fastq_files_zipped = list(self.path.glob(f'{self.accession}*.fastq.gz'))
        if not fastq_files_zipped:
            raise FileNotFoundError(f"No files found for {self.accession}")

        self._unzip(file_paths=fastq_files_zipped)
        fastq_files_unzipped = list(self.path.glob(f'{self.accession}*.fastq'))

        if not fastq_files_unzipped:
            raise FileNotFoundError(f"No files found for {self.accession}")

        return fastq_files_unzipped

    def __exit__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        if self.zipped:
            fastq_files = list(self.path.glob(f'{self.accession}*.fastq'))
            logger.debug('Removing unzipped temporary files...')
            for file in fastq_files:
                file.unlink()

    def _unzip(self, file_paths: list[Path]) -> None:
        """Unzip files."""
        if not file_paths:
            raise ValueError("No files have been given to unpigz")
        logger.debug("Unzipping %s...", "; ".join([str(file) for file in file_paths]))
        subprocess.run(
            ['unpigz', '--keep', '--processes', str(self.core_count), *file_paths], check=True
        )
