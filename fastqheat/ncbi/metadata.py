def download_metadata(
    *,
    filename: str,
    accession: list[str],
    attempts: int = 0,
    attempts_interval: int = 0,
) -> None:
    raise NotImplementedError
