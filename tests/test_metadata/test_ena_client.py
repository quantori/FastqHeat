import pytest
import requests
from requests.exceptions import RequestException

from fastqheat.backend.ena.metadata import ENAClient
from fastqheat.config import config
from tests.fixtures import MockResponse

accession_response = [
    {'run_accession': 'SRR7969880'},
    {'run_accession': 'SRR7969881'},
    {'run_accession': 'SRR7969882'},
]


def test_get_srr_ids_from_srp(mocker):
    """Check getting a list of SRRs by a given SRP."""
    accession = "SRP163674"

    ena_client = ENAClient()
    mock = mocker.patch.object(requests, "get", return_value=MockResponse(json=accession_response))
    srr_ids = ena_client.get_srr_ids_from_srp(accession)

    get_args = mock.call_args_list[0][1]

    assert get_args["params"]["accession"] == accession
    assert set(srr_ids) == {'SRR7969880', 'SRR7969881', 'SRR7969882'}


@pytest.mark.parametrize(
    ("ftp_flag", "aspera_flag", "fields", "json_response", "urls", "md5s"),
    [
        (
            True,  # ftp_flag
            False,  # aspera_flag
            "fastq_ftp,fastq_md5",  # fields
            [
                {
                    'run_accession': 'SRR7969986',
                    'fastq_ftp': 'ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz;ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',  # noqa: E501 line too long
                    'fastq_md5': '73242af9842bb15738713d57d4c45b28;152fffe3389fff996f983160eb213d86',  # noqa: E501 line too long
                }
            ],  # json_response - what should be returned by ENA api
            [
                'http://ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz',
                'http://ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',
            ],  # urls
            ['73242af9842bb15738713d57d4c45b28', '152fffe3389fff996f983160eb213d86'],  # md5s
        ),
        (
            False,  # ftp_flag
            True,  # aspera_flag
            "fastq_aspera,fastq_md5",  # fields
            [
                {
                    'run_accession': 'SRR7969986',
                    'fastq_aspera': 'fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz;fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',  # noqa: E501 line too long
                    'fastq_md5': '73242af9842bb15738713d57d4c45b28;152fffe3389fff996f983160eb213d86',  # noqa: E501 line too long
                }
            ],  # json_response
            [
                'fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz',
                'fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',
            ],  # urls
            ['73242af9842bb15738713d57d4c45b28', '152fffe3389fff996f983160eb213d86'],
        ),  # md5s
    ],
)
def test_get_urls_and_md5s(mocker, ftp_flag, aspera_flag, fields, json_response, urls, md5s):
    """
    Tests get_urls_and_md5s()

    Test that get_urls_and_md5s() makes right requests and returns right output based on
    given flags.
    """
    ena_client = ENAClient()

    mock = mocker.patch.object(
        requests,
        "get",
        return_value=MockResponse(json=json_response),
    )

    urls, md5s = ena_client.get_urls_and_md5s(term="SRR7969986", ftp=ftp_flag, aspera=aspera_flag)

    get_args = mock.call_args_list[0][1]

    assert get_args["params"]["fields"] == fields

    assert urls == urls
    assert md5s == md5s


@pytest.mark.parametrize(
    ("ftp_flag", "aspera_flag", "fields", "json_response", "urls"),
    [
        (
            True,  # ftp_flag
            False,  # aspera_flag
            "fastq_ftp",  # fields
            [
                {
                    'run_accession': 'SRR7969986',
                    'fastq_ftp': 'ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz;ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',  # noqa: E501 line too long
                }
            ],  # json_response - what should be returned by ENA api
            [
                'http://ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz',
                'http://ftp.sra.ebi.ac.uk/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',
            ],  # urls
        ),
        (
            False,  # ftp_flag
            True,  # aspera_flag
            "fastq_aspera",  # fields
            [
                {
                    'run_accession': 'SRR7969986',
                    'fastq_aspera': 'fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz;fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',  # noqa: E501 line too long
                }
            ],  # json_response
            [
                'fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_1.fastq.gz',
                'fasp.sra.ebi.ac.uk:/vol1/fastq/SRR796/006/SRR7969986/SRR7969986_2.fastq.gz',
            ],  # urls
        ),
    ],
)
def test_get_urls(mocker, ftp_flag, aspera_flag, fields, json_response, urls):
    """
    Tests get_urls()

    Test that get_urls() makes right requests and returns right output based on
    given flags.
    """
    ena_client = ENAClient()

    mock = mocker.patch.object(
        requests,
        "get",
        return_value=MockResponse(json=json_response),
    )

    urls = ena_client.get_urls(term="SRR7969986", ftp=ftp_flag, aspera=aspera_flag)

    get_args = mock.call_args_list[0][1]

    assert get_args["params"]["fields"] == fields

    assert urls == urls


@pytest.mark.parametrize(("ftp_flag", "aspera_flag"), [(True, True), (False, False)])
def test_get_urls_and_md5s_no_flag_fail(ftp_flag, aspera_flag):
    """Tests there should be at least one True flag passed to the get_urls_and_md5s() method."""
    ena_client = ENAClient()

    with pytest.raises(ValueError):
        ena_client.get_urls_and_md5s(term="SRR7969986", ftp=ftp_flag, aspera=aspera_flag)


def test_get_read_count(mocker):
    """Test get read count by term."""
    ena_client = ENAClient()

    mock = mocker.patch.object(
        requests,
        "get",
        return_value=MockResponse(json=[{'run_accession': 'SRR7969986', 'read_count': '344516'}]),
    )

    count = ena_client.get_read_count(term="SRR7969986")
    assert count == 344516

    get_args = mock.call_args_list[0][1]
    assert get_args["params"]["fields"] == "read_count"


def test_get_run_check(mocker):
    read_count = '344516'
    ena_client = ENAClient()

    mock = mocker.patch.object(
        requests,
        "get",
        return_value=MockResponse(
            json=[
                {
                    'run_accession': 'SRR7969986',
                    'fastq_md5': '73242af9842bb15738713d57d4c45b28;152fffe3389fff996f983160eb213d86',  # noqa: E501 line too long
                    'read_count': read_count,
                }
            ]
        ),
    )

    md5s, count = ena_client.get_run_check(term="SRR7969986")
    assert md5s == ['73242af9842bb15738713d57d4c45b28', '152fffe3389fff996f983160eb213d86']
    assert count == int(read_count)

    get_args = mock.call_args_list[0][1]
    assert get_args["params"]["fields"] == "fastq_md5,read_count"


def test_backoff_on_get(mocker):
    """Tests if ENAClient._get() retries on RequestError."""

    mock = mocker.patch.object(
        requests, "get", side_effect=[RequestException("whatever"), MockResponse(status=200)]
    )  # first time raises an error, second time executes successfully

    ena_client = ENAClient(attempts=2)
    ena_client._get(params={"whatever": ""})

    assert mock.call_count == config.MAX_ATTEMPTS
