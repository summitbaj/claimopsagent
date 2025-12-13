import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.dataverse.mcp_client import DataverseMCPClient, get_mcp_client


@pytest.mark.asyncio
async def test_fetch_record_uses_read_query_and_returns_row():
    client = DataverseMCPClient()

    # Mock session and its call_tool to ensure it's not used for fetch
    mock_session = AsyncMock()
    # read_query should return list with one dict
    async def fake_read_query(sql):
        return [{"smvs_claimid": "123", "smvs_name": "Test"}]

    client.session = mock_session

    # Patch read_query on the instance
    client.read_query = AsyncMock(side_effect=fake_read_query)

    result = await client.fetch_record("smvs_claim", "123")
    assert isinstance(result, dict)
    assert result.get("smvs_claimid") == "123"

    # Ensure session.call_tool wasn't used (we no longer call fetch tool)
    assert not mock_session.call_tool.called


@pytest.mark.asyncio
async def test_fetch_record_no_rows_returns_empty_dict():
    client = DataverseMCPClient()
    mock_session = AsyncMock()
    client.session = mock_session
    client.read_query = AsyncMock(return_value=[])

    result = await client.fetch_record("smvs_claim", "does-not-exist")
    assert result == {}
    assert not mock_session.call_tool.called
