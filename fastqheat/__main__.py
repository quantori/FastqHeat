import configparser
import functools
import logging
import os
import os.path
import re
import subprocess
import typing as tp

import backoff
import click

import fastqheat.ena as ena_module
import fastqheat.ncbi as ncbi_module
from fastqheat import __version__
from fastqheat.config import config
from fastqheat.ena.ena_api_client import ENAClient
from fastqheat.utility import get_cpu_cores_count

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level='DEBUG', datefmt="%H:%M:%S"
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


SRR_PATTERN = re.compile(r'^(SRR|ERR|DRR)\d+$')
SRP_PATTERN = re.compile(r'^(((SR|ER|DR)[PAXS])|(SAM(N|EA|D))|PRJ(NA|EB|DB)|(GS[EM]))\d+$')
USABLE_CPUS_COUNT = get_cpu_cores_count()

subprocess_run = backoff.on_exception(
    backoff.constant, subprocess.CalledProcessError, max_tries=lambda: config.MAX_ATTEMPTS
)(subprocess.run)


def get_program_version(program_name: str) -> tp.Optional[str]:
    try:
        result = subprocess.run(
            [program_name, '--version'], text=True, capture_output=True, check=True
        )
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr or e.stdout)
        raise
    else:
        output = result.stdout.strip()
        if program_name == 'ascp':
            return output.splitlines()[0]
        return output


def _make_accession_list(terms: tp.Iterable[str]) -> list[str]:
    """Get an accession list based on pattern of the given term."""
    accession_list = list()
    for term in terms:
        if not term:
            continue
        if SRR_PATTERN.search(term):
            accession_list.append(term)
        elif SRP_PATTERN.search(term):
            accession_list += ENAClient().get_srr_ids_from_srp(term)
        else:
            raise click.UsageError(f"Unknown accession pattern: {term}")
    return accession_list


@tp.no_type_check
def validate_accession(ctx, param, value: tp.Optional[str]) -> tp.Optional[list[str]]:
    if value:
        lst = re.split('[ ,]+', value)
        return _make_accession_list(lst)


@tp.no_type_check
def validate_accession_file(ctx, param, value) -> tp.Optional[list[str]]:
    if value:
        with open(value, 'r') as f:
            s = f.read()
            lines = s.splitlines(keepends=False)
        return _make_accession_list(lines)


@tp.no_type_check
def validate_config(ctx, param, value) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(value)
    if 'NCBI' not in config.keys():
        raise click.BadParameter(f"NCBI section not found in config {value}")
    if 'FasterQDump' not in config['NCBI'].keys():
        raise click.BadParameter(f"FasterQDump not found in NCBI section of config {value}")
    if 'ENA' not in config.keys():
        raise click.BadParameter(f"ENA section not found in config {value}")
    if 'SSHKey' not in config['ENA'].keys():
        raise click.BadParameter(f"SSHKey not found in ENA section of config {value}")
    if 'AsperaFASP' not in config['ENA'].keys():
        raise click.BadParameter(f"AsperaFASP not found in ENA section of config {value}")
    return config


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
        help='List of accessions separated by comma. E.g "111,222,333"',
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
        default=0,
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
    f = click.option(
        '--cpu-count',
        default=get_cpu_cores_count,
        show_default=True,
        help='Number of binaries or data checking threads to be working simultaneously.',
        type=click.IntRange(min=1),
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
    working_dir: str,
    metadata_file: str,
    config: configparser.ConfigParser,
    transport: str,
    accession: list[str],
    attempts: int,
    attempts_interval: int,
    cpu_count: int,
    skip_download: bool,
    skip_check: bool,
    skip_download_metadata: bool,
) -> None:
    if not skip_download:
        ena_module.download(
            accessions=accession,
            output_directory=working_dir,
            transport=transport,
            skip_check=skip_check,
            binary_path=config['ENA']['AsperaFASP'],
            attempts=attempts,
            attempts_interval=attempts_interval,
            cpu_count=cpu_count,
            aspera_ssh_path=config['ENA']['SSHKey.openssh'],
        )
    if skip_download and not skip_check:
        ena_module.check(
            directory=working_dir,
            accessions=accession,
            attempts=attempts,
            attempts_interval=attempts_interval,
            cpu_count=cpu_count,
        )
    if not skip_download_metadata:
        ena_module.download_metadata(
            directory=metadata_file,
            accession=accession,
            attempts=attempts,
            attempts_interval=attempts_interval,
            cpu_count=cpu_count,
        )


@click.command()
@common_options
@combine_accessions
def ncbi(
    working_dir: str,
    config: configparser.ConfigParser,
    accession: list[str],
    attempts: int,
    attempts_interval: int,
    cpu_count: int,
    skip_download: bool,
    skip_check: bool,
) -> None:
    if not skip_download:
        ncbi_module.download(
            output_directory=working_dir,
            binary_path=config['NCBI']['FasterQDump'],
            accessions=accession,
            attempts=attempts,
            attempts_timeout=attempts_interval,
            core_count=cpu_count,
        )
    if not skip_check:
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
