import hashlib
import logging
from functools import partial
from pathlib import Path

import fastqheat.typing_helpers as th
from fastqheat.ena.ena_api_client import ENAClient

logger = logging.getLogger("fastqheap.ena.check")


def md5_checksum(file_path: th.PathType, md5: str) -> bool:
    """
    Compare mdh5 hash of file to md5 value retrieved
    from ENA file report
    Parameters
    ----------
    file_path: str
        path to the file
    md5: str
        md5 hash retrieved from ENA file report
    Returns
    -------
    bool
        True if mdh5 hash of file matches md5 value retrieved
        from ENA file report, otherwise False
    """

    try:
        file = open(file_path, "rb")
    except FileNotFoundError:
        logging.warning('%s does not exist', file_path)
        return False

    md5_hash = hashlib.md5()
    chunk_size = md5_hash.block_size * 4_096

    with file as f:
        for byte_block in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(byte_block)

    return md5_hash.hexdigest() == md5


def check(
    *,
    directory: th.PathType,
    accessions: list[str],
    attempts: int,
    attempts_interval: int,
) -> bool:

    check_accession = partial(
        _check_accession,
        directory=directory,
        attempts=attempts,
        attempts_interval=attempts_interval,
    )
    return all(check_accession(accession) for accession in accessions)


def _check_accession(
    accession: str, directory: th.PathType, attempts: int, attempts_interval: int
) -> bool:
    """
    Takes an accession and check it against its md5

    directory - path to the folder where there is folder named by accession

    So it is `/some/output/directory/` part of the following structure:

    /some/output/directory/
    └── SRR7882015
        ├── SRR7882015_1.fastq.gz
        └── SRR7882015_2.fastq.gz
    """

    path = Path(directory) / accession  # e.g: /some/output/directory/SRR7882015
    logger.debug("Checking %s...", path)
    md5s = ENAClient(attempts=attempts, attempts_interval=attempts_interval).get_md5s(accession)
    fastq_files = sorted(list(path.glob(f'{accession}*.fastq.gz')))
    logger.debug("Found files:\n%s", "\n".join([str(file) for file in fastq_files]))

    return all((md5_checksum(file, md5) for file, md5 in zip(fastq_files, md5s)))
