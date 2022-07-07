from dataclasses import dataclass
from importlib.resources import files
from typing import Optional

from fastqheat.typing_helpers import PathLike


@dataclass
class Config:
    max_retries: int = 1
    aspera_private_key_path: PathLike = files(__package__) / 'asperaweb_id_dsa.openssh'


_config = Config()


def set_settings(
    *, max_retries: Optional[int] = None, aspera_private_key_path: Optional[str] = None
) -> None:
    if max_retries is not None:
        _config.max_retries = max_retries

    if aspera_private_key_path is not None:
        _config.aspera_private_key_path = aspera_private_key_path


def get_settings() -> Config:
    return _config
