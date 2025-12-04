"""Tests for asset handler functionality."""

import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest
from metadata.generator.asset_handler import get_release_asset_info
from metadata.generator.log_buffer import PluginLogBuffer

from .conftest import MockRelease, MockReleaseAsset


async def test_asset_not_found(mock_github: AsyncMock) -> None:
    """Test when asset is not found in release."""
    logger = PluginLogBuffer(Mock())
    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[
            MockReleaseAsset(
                name="other.zip",
                browser_download_url="https://example.com/other.zip",
                digest="sha256:abc123",
            )
        ],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)
    assert result is None


async def test_asset_with_size_only(mock_github: AsyncMock) -> None:
    """Test asset with size but no download count."""
    logger = PluginLogBuffer(Mock())
    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[
            MockReleaseAsset(
                name="plugin.zip",
                browser_download_url="https://example.com/plugin.zip",
                digest="sha256:abc123",
                size=1024,
            )
        ],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)
    assert result is not None
    assert result["size"] == 1024
    assert "download_count" not in result


async def test_asset_with_download_count_only(mock_github: AsyncMock) -> None:
    """Test asset with download count but no size."""
    logger = PluginLogBuffer(Mock())
    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[
            MockReleaseAsset(
                name="plugin.zip",
                browser_download_url="https://example.com/plugin.zip",
                digest="sha256:abc123",
                download_count=50,
            )
        ],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)
    assert result is not None
    assert result["download_count"] == 50
    assert "size" not in result


async def test_asset_no_download_url(mock_github: AsyncMock) -> None:
    """Test asset without digest or download URL."""
    logger = PluginLogBuffer(Mock())
    asset = type(
        "Asset",
        (),
        {
            "name": "plugin.zip",
            "browser_download_url": None,
            "url": None,
            "digest": None,
            "size": 2048,
            "download_count": 10,
        },
    )
    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[asset],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)
    assert result is not None
    assert "sha256" not in result
    assert result["size"] == 2048
    assert result["download_count"] == 10


async def test_asset_fallback_download_success(
    mock_github: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test successful fallback download and SHA256 calculation."""
    logger = PluginLogBuffer(Mock())

    # Mock session response
    content_data = b"test content for sha256"
    expected_sha256 = hashlib.sha256(content_data).hexdigest()

    # Create a proper mock for the async context manager
    class MockContent:
        async def iter_chunked(self, _size: int) -> AsyncIterator[bytes]:
            yield content_data

    class MockResponse:
        def __init__(self) -> None:
            self.content = MockContent()

        def raise_for_status(self) -> None:
            pass

        async def __aenter__(self) -> "MockResponse":
            return self

        async def __aexit__(self, *_args: object) -> None:
            pass

    class MockSession:
        def get(self, _url: str) -> MockResponse:
            return MockResponse()

        async def close(self) -> None:
            pass

    mock_session = MockSession()
    mock_github._session = mock_session

    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[
            MockReleaseAsset(
                name="plugin.zip",
                browser_download_url="https://example.com/plugin.zip",
                digest=None,  # No digest, will trigger fallback
                size=1024,
            )
        ],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)
    assert result is not None
    assert result["sha256"] == expected_sha256
    assert result["size"] == 1024


async def test_asset_fallback_download_failure(mock_github: AsyncMock) -> None:
    """Test fallback download failure handling."""
    logger = PluginLogBuffer(Mock())

    # Create a mock that raises an error
    class MockResponse:
        def raise_for_status(self) -> None:
            raise aiohttp.ClientError("Network error")

        async def __aenter__(self) -> "MockResponse":
            return self

        async def __aexit__(self, *_args: object) -> None:
            pass

    class MockSession:
        def get(self, _url: str) -> MockResponse:
            return MockResponse()

        async def close(self) -> None:
            pass

    mock_session = MockSession()
    mock_github._session = mock_session

    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[
            MockReleaseAsset(
                name="plugin.zip",
                browser_download_url="https://example.com/plugin.zip",
                digest=None,
                size=1024,
            )
        ],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)
    assert result is not None
    assert "sha256" not in result  # Should not have SHA256 on failure
    assert result["size"] == 1024


async def test_asset_fallback_no_session(
    mock_github: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test fallback when GitHubAPI has no session (creates its own)."""
    logger = PluginLogBuffer(Mock())

    # Remove _session from mock_github
    mock_github._session = None

    content_data = b"test content"
    expected_sha256 = hashlib.sha256(content_data).hexdigest()

    # Track if close was called
    close_called = False

    # Create a proper mock for the async context manager
    class MockContent:
        async def iter_chunked(self, _size: int) -> AsyncIterator[bytes]:
            yield content_data

    class MockResponse:
        def __init__(self) -> None:
            self.content = MockContent()

        def raise_for_status(self) -> None:
            pass

        async def __aenter__(self) -> "MockResponse":
            return self

        async def __aexit__(self, *_args: object) -> None:
            pass

    class MockSession:
        def get(self, _url: str) -> MockResponse:
            return MockResponse()

        async def close(self) -> None:
            nonlocal close_called
            close_called = True

    # Mock aiohttp.ClientSession to return our mock
    monkeypatch.setattr("aiohttp.ClientSession", MockSession)

    release = MockRelease(
        tag_name="v1.0.0",
        prerelease=False,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        published_at=datetime(2025, 1, 1, tzinfo=UTC),
        assets=[
            MockReleaseAsset(
                name="plugin.zip",
                browser_download_url="https://example.com/plugin.zip",
                digest=None,
                size=1024,
            )
        ],
    )

    result = await get_release_asset_info(mock_github, release, "plugin.zip", logger)

    assert result is not None
    assert result["sha256"] == expected_sha256
    # Verify session was closed
    assert close_called
