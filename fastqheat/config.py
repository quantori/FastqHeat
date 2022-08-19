from configparser import ConfigParser
from importlib.resources import files
from pathlib import Path

import click

from fastqheat.click_utils import check_binary_available


class FastQHeatConfigParser(ConfigParser):
    def __init__(self, *, filename: str, click_param: click.Parameter):
        super().__init__()
        read_ok = self.read(filename)
        self.validate_config()
        self.config_path = Path(read_ok[0]).absolute()
        self.click_param = click_param

    def validate_config(self) -> None:
        if 'NCBI' not in self.keys():
            raise click.BadParameter(
                f"NCBI section not found in config {self.config_path}",
                param=self.click_param,
            )
        if 'FasterQDump' not in self['NCBI'].keys():
            raise click.BadParameter(
                f"FasterQDump not found in NCBI section of config {self.config_path}",
                param=self.click_param,
            )
        if 'ENA' not in self.keys():
            raise click.BadParameter(
                f"ENA section not found in config {self.config_path}",
                param=self.click_param,
            )
        if 'SSHKey' not in self['ENA'].keys():
            raise click.BadParameter(
                f"SSHKey not found in ENA section of config {self.config_path}",
                param=self.click_param,
            )
        if 'AsperaFASP' not in self['ENA'].keys():
            raise click.BadParameter(
                f"AsperaFASP not found in ENA section of config {self.config_path}",
                param=self.click_param,
            )

    def validate_ena_binary_config(self) -> None:
        if not self.ena_ssh_key_path.is_file():
            raise click.BadParameter(
                f"""SSHKey file "{self.ena_ssh_key_path}" not found""",
                param=self.click_param,
            )
        check_binary_available(
            self.ena_binary_path,
            exception_cls=click.BadParameter,
            exception_kwargs={'param': self.click_param},
        )

    def validate_ncbi_binary_config(self) -> None:
        check_binary_available(
            self.ncbi_binary_path,
            exception_cls=click.BadParameter,
            exception_kwargs={'param': self.click_param},
        )

    @property
    def ena_ssh_key_path(self) -> Path:
        path = Path(self['ENA']['SSHKey'])
        if not path.is_absolute():
            return self.config_path.parent / path
        return path

    @property
    def ena_binary_path(self) -> str:
        return self['ENA']['AsperaFASP']

    @property
    def ncbi_binary_path(self) -> str:
        return self['NCBI']['FasterQDump']


class _Config:
    DEFAULT_MAX_ATTEMPTS: int = 2
    PATH_TO_ASPERA_KEY: str = str(files(__package__) / 'asperaweb_id_dsa.openssh')

    # How many requests we make simultaneously to ENA API during downloading metadata
    # What is the limit or sweet spot - we have not tested yet
    METADATA_DOWNLOAD_SIMULTANEOUS_CONNECTIONS_NUMBER: int = 5


config = _Config()
