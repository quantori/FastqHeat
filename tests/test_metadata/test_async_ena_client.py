from unittest.mock import AsyncMock

import pytest

from fastqheat.backend.ena.ena_api_client import ENAAsyncClient
from tests.fixtures import AsyncMockResponse, MockAsyncSession

fields_response = [
    {"columnId": "study_accession", "description": "study accession number"},
    {"columnId": "secondary_study_accession", "description": "secondary study accession number"},
]

metadata_response = [
    {
        'accession': 'SAMN10181503',
        'altitude': '',
        'assembly_quality': '',
        'assembly_software': '',
        'base_count': '22674621',
        'binning_software': '',
        'bio_material': 'soil',
        'broker_name': '',
    }
]


@pytest.mark.asyncio
async def test_get_ena_field():
    """Test happy path of method ENAAsyncClient.get_ena_field()."""
    ena_client = ENAAsyncClient()
    mock = AsyncMock(return_value=AsyncMockResponse(json=fields_response))
    ena_client.session = MockAsyncSession(get=mock)
    fields = await ena_client.get_ena_fields()

    assert await mock.called_once()
    url = mock.call_args_list[0][0][0]
    params = mock.call_args_list[0][1]["params"]
    assert url == ena_client._return_fields_url
    assert params == {'dataPortal': 'ena', 'result': 'read_run', 'format': 'json'}
    assert fields == ["study_accession", "secondary_study_accession"]


@pytest.mark.asyncio
async def test_get_metadata():
    """Test happy path of method ENAAsyncClient.get_metadata()."""

    dummy_fields = "some,some1,some2"
    accession = "SRR7969880"

    ena_client = ENAAsyncClient()
    mock = AsyncMock(return_value=AsyncMockResponse(json=metadata_response))
    ena_client.session = MockAsyncSession(get=mock)
    metadata = await ena_client.get_metadata(accession=accession, fields=dummy_fields)

    assert await mock.called_once()
    url = mock.call_args_list[0][0][0]
    params = mock.call_args_list[0][1]["params"]
    assert url == ena_client._filereport_url
    assert params == {
        'result': 'read_run',
        'format': 'json',
        "fields": dummy_fields,
        "accession": accession,
    }

    assert metadata == metadata_response
