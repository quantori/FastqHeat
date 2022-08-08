from importlib.resources import files


class _Config:
    DEFAULT_MAX_ATTEMPTS: int = 2
    PATH_TO_ASPERA_KEY: str = str(files(__package__) / 'asperaweb_id_dsa.openssh')

    # How many requests we make simultaneously to ENA API during downloading metadata
    # What is the limit or sweet spot - we have not tested yet
    METADATA_DOWNLOAD_SIMULTANEOUS_CONNECTS_NUMBER_SIZE: int = 5


config = _Config()
