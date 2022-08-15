import asyncio
import functools
import logging
import os
import os.path
import re
import subprocess
import typing as tp
from pathlib import Path

import backoff
import click

import fastqheat.backend.ena as ena_module
import fastqheat.backend.ncbi as ncbi_module
from fastqheat import __version__
from fastqheat.backend.ena.ena_api_client import ENAClient
from fastqheat.config import FastQHeatConfigParser, config
from fastqheat.exceptions import ENAClientError
from fastqheat.utility import get_cpu_cores_count

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(lineno)s:%(message)s",
    level='DEBUG',
    datefmt="%H:%M:%S",
)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger("fastqheat.main")

SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')
USABLE_CPUS_COUNT = get_cpu_cores_count()

subprocess_run = backoff.on_exception(
    backoff.constant, subprocess.CalledProcessError, max_tries=lambda: config.DEFAULT_MAX_ATTEMPTS
)(subprocess.run)


def _make_accession_list(terms: tp.Iterable[str]) -> list[str]:
    """Get an accession list based on pattern of the given term."""
    accession_list = list()
    for term in terms:
        # validate_accession_file may return some empty strings.
        # Here is the easiest place to deal with it.
        if not term:
            continue
        if SRR_PATTERN.search(term):
            accession_list.append(term)
        elif SRP_PATTERN.search(term):
            try:
                accession_list += ENAClient().get_srr_ids_from_srp(term)
            except ENAClientError:
                # We handle this error in ENAClient().get_srr_ids_from_srp(term)
                # Here we only need to catch it in order to skip the current term and proceed
                # with the next one instead of crushing
                continue
        else:
            raise click.UsageError(f"Unknown accession pattern: {term}")
    return accession_list


def validate_accession(
    ctx: click.core.Context, param: click.core.Option, value: tp.Optional[str]
) -> tp.Optional[list[str]]:
    if not value:
        return None
    lst = re.split('[ ,]+', value)
    return _make_accession_list(lst)


def validate_accession_file(
    ctx: click.core.Context,
    param: click.core.Option,
    value: tp.Optional[str],
) -> tp.Optional[list[str]]:
    if not value:
        return None
    with open(value, 'r') as f:
        s = f.read()
        lines = s.splitlines(keepends=False)
    return _make_accession_list(lines)


@tp.no_type_check
def validate_config(ctx, param, value) -> FastQHeatConfigParser:
    return FastQHeatConfigParser(filename=value, click_param=param)


def common_options(f: tp.Callable) -> tp.Callable:
    f = click.option(
        '--working-dir',
        default=os.getcwd,
        type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
        show_default=True,
        help='Working directory.',
    )(f)
    f = click.option(
        '--config',
        default=get_config_path,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
        callback=validate_config,
        show_default=True,
        help='Configuration file path.',
    )(f)
    f = click.option(
        '--accession',
        default=[],
        show_default=True,
        callback=validate_accession,
        help='List of accessions separated by comma. E.g "SRP163674,SRR7969880,SRP163674"',
    )(f)
    f = click.option(
        '--accession-file',
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
        show_default=True,
        callback=validate_accession_file,
        help='File with accessions separated by a newline.',
    )(f)
    f = click.option(
        '--attempts',
        default=config.DEFAULT_MAX_ATTEMPTS,
        show_default=True,
        help='Retry attempts in case of network error.',
        type=click.IntRange(min=0),
    )(f)
    f = click.option(
        '--attempts_interval',
        default=0,
        show_default=True,
        help='Retry attempts interval in seconds in case of network error.',
        type=click.IntRange(min=0),
    )(f)
    f = click.option(
        '--skip-download',
        default=False,
        show_default=True,
        help='Skip data download step. Data check (if not skipped) will '
        'expect data to be in the working directory',
        type=click.BOOL,
    )(f)
    f = click.option(
        '--skip-check',
        default=False,
        show_default=True,
        help='Skip data check step.',
    )(f)
    return f


def get_config_path() -> str:
    return os.path.join(os.path.dirname(__file__), 'config.conf')


def get_metadata_file() -> str:
    return os.path.join(os.getcwd(), 'metadata.csv')


@tp.no_type_check
def combine_accessions(f: tp.Callable):
    @functools.wraps(f)
    def wrapped(*args, accession: tp.Optional[list], accession_file: tp.Optional[list], **kwargs):
        if not accession and not accession_file:
            raise click.UsageError('No accessions specified')
        accession = (accession or []) + (accession_file or [])
        return f(*args, accession=accession, **kwargs)

    return wrapped


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """
    This help message is also accessible via `python3 -m fastqheat --help`.

    ## Compatibility

    FastqHeat is being developed and tested under Python 3.9.x.

    ## Installation

     1. [Make sure you have installed a supported version of Python]
     (https://www.python.org/downloads/).

     2. Clone this project from GitHub or download it as an archive.

     3. **Optional, but recommended:** create and activate a fresh
     [virtual environment]
     (https://docs.python.org/3/library/venv.html#creating-virtual-environments).

     4. Install it directly with `pip`.

    Full example for Linux systems:

    bash:

    $ git clone git@github.com:quantori/FastqHeat.git

    $ python3 -m venv env

    $ . env/bin/activate

    $ pip install FastqHeat/
    """
    pass


@click.command()
@common_options
@click.option(
    '--transport',
    default='binary',
    show_default=True,
    help='Transport (method) to be user to download data.',
    type=click.Choice(['binary', 'ftp'], case_sensitive=False),
)
@click.option(
    '--metadata-file',
    default=get_metadata_file,
    show_default=True,
    help='Metadata filepath',
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True),
)
@click.option(
    '--skip-download-metadata',
    default=False,
    show_default=True,
    help='Skip metadata download step',
)
@combine_accessions
def ena(
    working_dir: Path,
    metadata_file: str,
    config: FastQHeatConfigParser,
    transport: str,
    accession: list[str],
    attempts: int,
    attempts_interval: int,
    skip_download: bool,
    skip_check: bool,
    skip_download_metadata: bool,
) -> None:
    if not skip_download:
        if transport == 'binary':
            config.validate_ena_binary_config()
        ena_module.download(
            accessions=accession,
            output_directory=working_dir,
            transport=transport,
            skip_check=skip_check,
            binary_path=config.ena_binary_path,
            attempts=attempts,
            attempts_interval=attempts_interval,
            aspera_ssh_path=config.ena_ssh_key_path,
        )
    if skip_download and not skip_check:
        ena_module.check(
            directory=working_dir,
            accessions=accession,
            attempts=attempts,
            attempts_interval=attempts_interval,
        )
    if not skip_download_metadata:
        asyncio.run(
            ena_module.download_metadata(
                directory=metadata_file,
                accession=accession,
                attempts=attempts,
                attempts_interval=attempts_interval,
            )
        )


@click.command()
@common_options
@click.option(
    '--cpu-count',
    default=get_cpu_cores_count,
    show_default=True,
    help='Sets the amount of cpu-threads used by fasterq-dump (binary that downloads files from'
    ' NCBI) and pigz (binary that zips files)',
    type=click.IntRange(min=1),
)
@combine_accessions
def ncbi(
    working_dir: Path,
    config: FastQHeatConfigParser,
    accession: list[str],
    attempts: int,
    attempts_interval: int,
    cpu_count: int,
    skip_download: bool,
    skip_check: bool,
) -> None:
    if not skip_download:
        config.validate_ncbi_binary_config()
        ncbi_module.download(
            output_directory=working_dir,
            binary_path=config.ncbi_binary_path,
            accessions=accession,
            attempts=attempts,
            skip_check=skip_check,
            attempts_interval=attempts_interval,
            core_count=cpu_count,
        )
    if skip_download and not skip_check:
        ncbi_module.check(
            directory=working_dir,
            accessions=accession,
            attempts=attempts,
            attempts_interval=attempts_interval,
            core_count=cpu_count,
        )


cli.add_command(ena)
cli.add_command(ncbi)

if __name__ == '__main__':
    cli()
