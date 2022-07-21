import logging

from fastqheat.ncbi import check, download

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level='DEBUG')
logging.getLogger("urllib3").setLevel(logging.WARNING)

if __name__ == '__main__':
    result = download(
        accessions=["SRR7969880"],
        output_directory="./ncbi_test",
        attempts=1,
        attempts_timeout=1,
        # transport="aspera",
    )
    if result:
        print("downloaded successfully")
    else:
        print("something went wrong")

    # result = check(
    #     directory="./ncbi_test",
    #     accessions=["SRR7969880"],
    #     attempts=1,
    #     attempts_interval=1,
    #     core_count=6,
    # )
    # if result:
    #     print("checked successfully")
    # else:
    #     print("something went wrong")
