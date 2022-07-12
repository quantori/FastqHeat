from importlib.resources import files


class _Config:
    # 1 - in the backoff library means no retries at all
    # 2 - if code failed once, backoff library will try to execute it again 1 time
    # so I guess in backoff library means not MAX_RETRIES but MAX_TRIES
    MAX_RETRIES: int = 3
    PATH_TO_ASPERA_KEY: str = str(files(__package__) / 'asperaweb_id_dsa.openssh')


config = _Config()
