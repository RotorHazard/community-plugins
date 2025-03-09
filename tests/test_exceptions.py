"""Test exceptions in the generate_metadata script."""

import base64
import json
from unittest.mock import AsyncMock

import pytest
from aiogithubapi import (
    GitHubNotFoundException,
    GitHubRatelimitException,
)
from metadata.plugin_metadata_generator import PluginMetadataGenerator

from . import load_fixture
from .conftest import MockGitHubResponse


@pytest.mark.asyncio
async def test_fetch_repository_info_not_found(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test repository not found exception in the PluginMetadataGenerator class."""

    async def get_raise(repo_name: str) -> None:
        raise GitHubNotFoundException("Repository not found")

    monkeypatch.setattr(mock_github.repos, "get", get_raise)
    plugin = PluginMetadataGenerator("owner/nonexistent")
    result = await plugin.fetch_repository_info(mock_github)
    assert result is False


@pytest.mark.asyncio
async def test_fetch_repository_info_rate_limit(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test rate limit exception in the PluginMetadataGenerator class."""

    async def get_rate_limit(repo_name: str) -> None:
        raise GitHubRatelimitException("Rate limit exceeded")

    monkeypatch.setattr(mock_github.repos, "get", get_rate_limit)
    plugin = PluginMetadataGenerator("owner/repo")
    result = await plugin.fetch_repository_info(mock_github)
    assert result is False


@pytest.mark.asyncio
async def test_fetch_manifest_file_json_decode_error(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the PluginMetadataGenerator class with a JSON decode error."""

    async def get_bad_manifest(
        repo_name: str,
        path: str,
        ref: str | None = None,
        etag: str | None = None,
    ) -> MockGitHubResponse:
        content = base64.b64encode(b"not a json").decode("utf-8")
        file_data = type("Data", (), {"content": content})
        return MockGitHubResponse(data=file_data, etag="mock_manifest_etag")

    monkeypatch.setattr(mock_github.repos.contents, "get", get_bad_manifest)
    plugin = PluginMetadataGenerator("owner/repo")
    result = await plugin.fetch_manifest_file(mock_github)
    assert result is False


@pytest.mark.asyncio
async def test_fetch_manifest_file_not_found(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the PluginMetadataGenerator class with a missing manifest file."""

    async def get_raise(
        repo_name: str,
        path: str,
        ref: str | None = None,
        etag: str | None = None,
    ) -> None:
        raise GitHubNotFoundException("Manifest file not found")

    monkeypatch.setattr(mock_github.repos.contents, "get", get_raise)
    plugin = PluginMetadataGenerator("owner/repo")
    result = await plugin.fetch_manifest_file(mock_github)
    assert result is False


@pytest.mark.asyncio
async def test_validate_manifest_domain_exception(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test on a manifest with an invalid domain set as the plugin domain."""
    original_get = mock_github.repos.contents.get

    async def get_manifest(
        repo_name: str,
        path: str = "",
        ref: str | None = None,
        etag: str | None = None,
    ) -> MockGitHubResponse:
        if not path:
            path = "custom_plugins"
        if path == "custom_plugins/testdomain/manifest.json":
            content = base64.b64encode(
                json.dumps(load_fixture("wrong_domain_manifest.json")).encode("utf-8")
            ).decode("utf-8")
            file_data = type("Data", (), {"content": content})
            return MockGitHubResponse(data=file_data, etag="mock_manifest_etag")
        return await original_get(repo_name, path, ref, etag)

    monkeypatch.setattr(mock_github.repos.contents, "get", get_manifest)

    plugin = PluginMetadataGenerator("owner/repo")

    await plugin.fetch_repository_info(mock_github)
    await plugin.fetch_github_releases(mock_github)
    await plugin.validate_plugin_repository(mock_github)
    manifest_fetched = await plugin.fetch_manifest_file(mock_github)
    assert manifest_fetched is True
    valid_domain = await plugin.validate_manifest_domain()
    assert valid_domain is False
