from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    max_retries: int = 1


_config = Config()


def set_settings(*, max_retries: Optional[int] = None) -> None:
    if max_retries is not None:
        _config.max_retries = max_retries


def get_settings() -> Config:
    return _config
