"""Tests for the Generate Metadata script."""

import base64
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from scripts.generate_metadata import PluginMetadataGenerator, SummaryGenerator
from syrupy.assertion import SnapshotAssertion

from . import load_fixture
from .conftest import MockGitHubResponse, MockRepo


@pytest.mark.asyncio
@pytest.mark.freeze_time("2025-03-09 15:00:00+01:00")
async def test_rotorhazard_plugin_success(
    mock_github: AsyncMock, snapshot: SnapshotAssertion
) -> None:
    """Test the PluginMetadataGenerator class with a successful repository."""
    plugin = PluginMetadataGenerator("owner/repo")
    metadata = await plugin.fetch_metadata(mock_github)
    # Check if the metadata is not empty
    assert metadata is not None
    repo_id, data = next(iter(metadata.items()))
    assert "manifest" in data
    assert data["manifest"]["name"] == "Test Plugin"
    assert data["domain"] == "testdomain"

    snapshot.assert_match(data)


@pytest.mark.asyncio
async def test_rotor_hazard_plugin_archived(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the PluginMetadataGenerator class with an archived repository."""

    # Patch the GitHubAPI class to return the mock_github instance
    async def archived_get(repo_name: str) -> MockGitHubResponse:
        repo = MockRepo(
            full_name=repo_name,
            archived=True,
            updated_at=datetime.now(UTC).isoformat(),
            open_issues_count=5,
            stargazers_count=100,
            topics=["python", "plugin"],
            id=1,
        )
        return MockGitHubResponse(data=repo, etag="mock_repo_etag")

    monkeypatch.setattr(mock_github.repos, "get", archived_get)
    plugin = PluginMetadataGenerator("owner/repo_archived")
    metadata = await plugin.fetch_metadata(mock_github)
    assert metadata is not None
    repo_id, data = next(iter(metadata.items()))
    # Expect the plugin to be archived
    assert data.get("archived") is True


@pytest.mark.asyncio
async def test_manifest_domain_mismatch(
    mock_github: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test the PluginMetadataGenerator class with a mismatched manifest domain."""
    original_get = mock_github.repos.contents.get

    async def wrong_manifest_get(
        repo_name: str,
        path: str = "custom_plugins",
        ref: str | None = None,
        etag: str | None = None,
    ) -> MockGitHubResponse:
        if path == "custom_plugins/testdomain/manifest.json":
            content = base64.b64encode(
                json.dumps(load_fixture("wrong_domain_manifest.json")).encode("utf-8")
            ).decode("utf-8")
            file_data = type("Data", (), {"content": content})
            return MockGitHubResponse(data=file_data, etag="mock_manifest_etag")
        return await original_get(repo_name, path, ref, etag)

    monkeypatch.setattr(mock_github.repos.contents, "get", wrong_manifest_get)
    plugin = PluginMetadataGenerator("owner/repo")
    await plugin.fetch_repository_info(mock_github)
    await plugin.fetch_github_releases(mock_github)
    await plugin.validate_plugin_repository(mock_github)
    manifest_fetched = await plugin.fetch_manifest_file(mock_github)
    assert manifest_fetched is True
    valid_domain = await plugin.validate_manifest_domain()
    assert valid_domain is False
    monkeypatch.setattr(mock_github.repos.contents, "get", original_get)


@pytest.mark.asyncio
async def test_manifest_version_mismatch(
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the PluginMetadataGenerator class with a mismatched manifest version."""
    original_get = mock_github.repos.contents.get

    async def wrong_version_get(
        repo_name: str,
        path: str = "custom_plugins",
        ref: str | None = None,
        etag: str | None = None,
    ) -> MockGitHubResponse:
        if path == "custom_plugins/testdomain/manifest.json":
            content = base64.b64encode(
                json.dumps(load_fixture("wrong_version_manifest.json")).encode("utf-8")
            ).decode("utf-8")
            file_data = type("Data", (), {"content": content})
            return MockGitHubResponse(data=file_data, etag="mock_manifest_etag")
        return await original_get(repo_name, path, ref, etag)

    monkeypatch.setattr(mock_github.repos.contents, "get", wrong_version_get)
    plugin = PluginMetadataGenerator("owner/repo")
    await plugin.fetch_repository_info(mock_github)
    await plugin.fetch_github_releases(mock_github)
    await plugin.validate_plugin_repository(mock_github)
    await plugin.fetch_manifest_file(mock_github)
    valid_version = await plugin.validate_manifest_version()
    assert valid_version is False
    monkeypatch.setattr(mock_github.repos.contents, "get", original_get)


@pytest.mark.asyncio
async def test_metadata_generator(
    tmp_path: Path,
    plugins_file: Path,
    mock_github: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the MetadataGenerator class."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    # Create a diff directory to store the diff files
    (output_dir / "diff").mkdir(parents=True, exist_ok=True)

    # Patch the GitHubAPI class to return the mock_github instance
    monkeypatch.setattr("aiogithubapi.GitHubAPI", AsyncMock(return_value=mock_github))
    summary = SummaryGenerator(str(plugins_file), str(output_dir))
    await summary.generate()

    # Check if the output files are created
    data_file = output_dir / "data.json"
    repos_file = output_dir / "repositories.json"
    summary_file = output_dir / "summary.json"
    assert data_file.exists()
    assert repos_file.exists()
    assert summary_file.exists()

    data = json.loads(data_file.read_text())
    repos = json.loads(repos_file.read_text())
    summary = json.loads(summary_file.read_text())

    assert isinstance(data, dict)
    assert isinstance(repos, list)
    assert "total_plugins" in summary
    snapshot.assert_match(summary)
