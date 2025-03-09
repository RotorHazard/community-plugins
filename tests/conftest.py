"""Globale fixtures for the tests."""

import base64
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from . import load_fixture


@dataclass
class MockGitHubResponse:
    """Mock GitHub response."""

    data: Any
    etag: str = "mock_etag"


@dataclass
class MockRepo:
    """Mock GitHub repository."""

    full_name: str
    archived: bool = False
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    open_issues_count: int = 0
    stargazers_count: int = 10
    topics: list[str] = field(default_factory=list)
    id: int = 123456


@dataclass
class MockRelease:
    """Mock GitHub release."""

    tag_name: str
    prerelease: bool
    created_at: datetime


def create_mock_repos(
    mock_repos_releases: MagicMock,
    mock_repos_contents: MagicMock,
) -> MagicMock:
    """Create a mock GitHubAPI.repos object."""
    mock = MagicMock()
    # Simulate the GitHubAPI.repos.get method
    mock.get = AsyncMock()
    mock.get.return_value = MockGitHubResponse(
        data=MockRepo(
            full_name="owner/repo",
            archived=False,
            updated_at=datetime.now(UTC).isoformat(),
            open_issues_count=5,
            stargazers_count=100,
            topics=["python", "plugin"],
            id=1,
        ),
        etag="mock_repo_etag",
    )
    mock.releases = MagicMock()
    mock.releases.list = mock_repos_releases
    mock.contents = MagicMock()
    mock.contents.get = mock_repos_contents
    return mock


@pytest.fixture
def mock_repos_releases() -> MagicMock:
    """Fixture to mock the GitHubAPI.repos.releases.list method."""

    async def list_releases(repo_name: str) -> MockGitHubResponse:
        now = datetime.now(UTC)
        # Eerst een prerelease en daarna een stabiele release
        stable = MockRelease("v1.0.1", False, now - timedelta(days=1))  # noqa: FBT003
        prerelease = MockRelease("v1.0.2-beta", True, now)  # noqa: FBT003
        return MockGitHubResponse(data=[prerelease, stable], etag="mock_release_etag")

    return AsyncMock(side_effect=list_releases)


@pytest.fixture
def mock_repos_contents() -> MagicMock:
    """Fixture to mock the GitHubAPI.repos.contents.get method."""

    async def get_contents(
        repo_name: str,
        path: str = "custom_plugins",
        ref: str | None = None,
        etag: str | None = None,
    ) -> MockGitHubResponse:
        # Define a dataclass for the folder item
        @dataclass
        class FolderItem:
            name: str
            type: str

        if path == "custom_plugins":
            if ref is not None:
                return MockGitHubResponse(data=[FolderItem("custom_plugins", "dir")])
            return MockGitHubResponse(data=[FolderItem("testdomain", "dir")])
        if path == "custom_plugins/testdomain/manifest.json":
            # Bouw de response voor het manifest bestand
            content = base64.b64encode(
                json.dumps(load_fixture("manifest_data.json")).encode("utf-8")
            ).decode("utf-8")
            file_data = type("Data", (), {"content": content})
            return MockGitHubResponse(data=file_data, etag="mock_manifest_etag")
        raise Exception("File not found")  # noqa: TRY002

    return AsyncMock(side_effect=get_contents)


@pytest.fixture
def plugins_file(tmp_path: Path) -> Path:
    """Fixture to create a plugins.json file."""
    plugins = ["owner/repo", "owner/repo_archived"]
    file = tmp_path / "plugins.json"
    file.write_text(json.dumps(plugins))
    return file


@pytest.fixture
def mock_repos(
    mock_repos_releases: MagicMock,
    mock_repos_contents: MagicMock,
) -> MagicMock:
    """Fixture to mock the GitHubAPI.repos object."""
    return create_mock_repos(mock_repos_releases, mock_repos_contents)


@pytest.fixture
def mock_github(
    monkeypatch: pytest.MonkeyPatch,
    mock_repos_releases: MagicMock,
    mock_repos_contents: MagicMock,
) -> MagicMock:
    """Mock GitHubAPI for testing."""
    mock_repos_obj = create_mock_repos(mock_repos_releases, mock_repos_contents)

    class MockGitHubAPIForTest:
        def __init__(self, token: str | None = None) -> None:
            self.token = token
            self.repos = mock_repos_obj

        async def __aenter__(self) -> MagicMock:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            pass

    monkeypatch.setattr(
        "aiogithubapi.GitHubAPI", lambda token=None: MockGitHubAPIForTest(token)
    )
    return MockGitHubAPIForTest()
