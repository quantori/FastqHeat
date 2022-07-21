from fastqheat.ena.ena_api_client import ENAClient


def download_metadata(
    *, accessions: list[str], attempts: int = 0, attempts_interval: int = 0, **kwargs
):
    ena_client = ENAClient(  # noqa:  F841 local variable 'ena_client' is assigned to but never used
        attempts=attempts, attempts_interval=attempts_interval
    )

    raise NotImplementedError
