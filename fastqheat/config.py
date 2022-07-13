from importlib.resources import files


class _Config:
    MAX_ATTEMPTS: int = 2
    PATH_TO_ASPERA_KEY: str = str(files(__package__) / 'asperaweb_id_dsa.openssh')


config = _Config()
