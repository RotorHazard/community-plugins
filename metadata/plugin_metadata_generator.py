"""Generate metadata for each RotorHazard community plugin."""

import base64
import json
import logging
from datetime import UTC, datetime

from aiogithubapi import (
    GitHubAPI,
    GitHubException,
    GitHubNotFoundException,
    GitHubRatelimitException,
)
from const import EXCLUDED_KEYS, LOGGER


class PluginLogBuffer:
    """Buffer logs per plugin before printing them grouped."""

    def __init__(self, repo: str) -> None:
        """Initialize the log buffer for a specific plugin repository."""
        self.repo = repo
        self.buffer: list[tuple[int, str]] = []

    def log(self, level: int, message: str) -> None:
        """Buffer a log message with its level."""
        self.buffer.append((level, message))

    def flush(self) -> None:
        """Flush the buffered logs to the logger."""
        LOGGER.info(f"::group::🔧 {self.repo}")
        for level, message in self.buffer:
            LOGGER.log(level, f"<{self.repo}> {message}")
        LOGGER.info("::endgroup::")


class PluginMetadataGenerator:
    """Generate metadata for each RotorHazard community plugin."""

    def __init__(self, repo: str) -> None:
        """Initialize the plugin metadata generator."""
        self.repo = repo  # Full repository name (e.g., "owner/repo_name")
        self.domain = None  # Plugin domain folder
        self.metadata = {}
        self.manifest_data = {}
        self.repo_metadata = {}
        self.etag_repository = None
        self.etag_release = None
        self.releases = []
        self.logger = PluginLogBuffer(repo)

    def log(self, message: str, level: int = logging.INFO) -> None:
        """Log a message with the specified level, buffering it for later."""
        self.logger.log(level, message)

    @property
    def latest_stable(self) -> str | None:
        """Return the latest stable release."""
        return next((r.tag_name for r in self.releases if not r.prerelease), None)

    @property
    def latest_prerelease(self) -> str | None:
        """Return the latest pre-release."""
        return next((r.tag_name for r in self.releases if r.prerelease), None)

    @property
    def used_ref(self) -> str:
        """Return the branch/tag name used for fetching metadata."""
        if self.releases:
            return self.releases[0].tag_name
        return self.repo_metadata.default_branch

    async def fetch_repository_info(self, github: GitHubAPI) -> bool:
        """Fetch and store repository metadata from GitHub.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            bool: True if the repository data is fetched successfully, False otherwise.

        """
        self.log("🔎 Fetching repository metadata...")
        try:
            repo_response = await github.repos.get(self.repo)
            self.repo = repo_response.data.full_name
            self.repo_metadata = repo_response.data
        except GitHubRatelimitException:
            self.log(
                "GitHub API rate limit exceeded. Please retry later.", logging.ERROR
            )
            return False
        except GitHubNotFoundException:
            self.log("Repository not found on GitHub.", logging.ERROR)
            return False
        except GitHubException:
            self.log("Failed to retrieve repository information.", logging.ERROR)
            return False
        self.etag_repository = repo_response.etag
        return True

    async def fetch_github_releases(self, github: GitHubAPI) -> bool:
        """Fetch the latest stable and prerelease versions from GitHub.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            bool: True if the releases are fetched successfully, False otherwise.

        """
        self.log("🔎 Fetching GitHub releases...")
        try:
            releases = await github.repos.releases.list(self.repo)
            if releases.etag:
                self.etag_release = releases.etag
            if not releases.data:
                self.log("No releases found.", logging.WARNING)
                return False

            # Ensure releases are sorted by creation date (newest first)
            self.releases = sorted(
                releases.data, key=lambda r: r.created_at, reverse=True
            )
        except GitHubException:
            self.log("Error occurred while fetching releases.", logging.ERROR)
            return False

        # Log the latest stable and prerelease versions
        message = f"ℹ️  Latest stable release: {self.latest_stable}"  # noqa: RUF001
        if self.latest_prerelease:
            message += f", Latest pre-release: {self.latest_prerelease}"
        self.log(message)
        return True

    async def fetch_manifest_file(self, github: GitHubAPI) -> bool:
        """Fetch the manifest file from the repository.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            bool: True if the manifest file is fetched successfully, False otherwise.

        """
        manifest_path = f"custom_plugins/{self.domain}/manifest.json"
        self.log(f"🔎 Fetching plugin domain folder (branch: {self.used_ref})")
        try:
            response = await github.repos.contents.get(
                self.repo, f"{manifest_path}?ref={self.used_ref}"
            )
            content = base64.b64decode(response.data.content).decode("utf-8")
            self.manifest_data = json.loads(content)
            self.log(f"✅ Successfully fetched manifest.json (branch: {self.used_ref})")
        except (GitHubNotFoundException, json.JSONDecodeError, GitHubException):
            self.log(
                f"Failed to fetch `{manifest_path}` from {self.used_ref}.",
                logging.ERROR,
            )
            return False
        return True

    async def validate_plugin_repository(self, github: GitHubAPI) -> bool:
        """Fetch the plugin domain folder and validate the repository structure.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            bool: True if the plugin domain is fetched successfully, False otherwise.

        """
        try:
            self.log(f"🔎 Fetching plugin domain folder (branch: {self.used_ref})")
            response = await github.repos.contents.get(
                self.repo, f"?ref={self.used_ref}"
            )

            # Check for `custom_plugins/` folder
            custom_plugins_folder = next(
                (
                    item
                    for item in response.data
                    if item.name == "custom_plugins" and item.type == "dir"
                ),
                None,
            )
            if not custom_plugins_folder:
                self.log("Missing `custom_plugins/` folder.", logging.ERROR)
                return False

            # Fetch the contens of the `custom_plugins/` folder
            folder_response = await github.repos.contents.get(
                self.repo, f"custom_plugins?ref={self.used_ref}"
            )
            subfolders = [item for item in folder_response.data if item.type == "dir"]

            # Ensure there is exactly one domain folder
            if len(subfolders) != 1:
                self.log(
                    "Expected one domain folder in "
                    f"`custom_plugins/`, found: {len(subfolders)}.",
                    logging.ERROR,
                )
                return False

            self.domain = subfolders[0].name
        except GitHubNotFoundException:
            self.log("Repository not found.", logging.WARNING)
            return False
        except GitHubException:
            self.log("Error fetching plugin domain.", logging.ERROR)
            return False
        self.log(f"ℹ️  Plugin domain folder: `{self.domain}` (branch: {self.used_ref})")  # noqa: RUF001
        return True

    async def validate_manifest_domain(self) -> bool:
        """Validate that the domain in `manifest.json` matches the folder name.

        Returns
        -------
            bool: True if the domain matches the folder name, False otherwise.

        """
        # Check if the domain in manifest.json matches the folder name
        manifest_domain: str = self.manifest_data.get("domain")
        if manifest_domain != self.domain:
            self.log(
                f"Domain mismatch: Folder '{self.domain}' "
                f"vs Manifest '{manifest_domain}'",
                logging.ERROR,
            )
            return False
        # Manifest domain matches the folder name
        self.log(
            f"✅ Manifest domain validated: '{manifest_domain}' matches domain folder"
        )
        return True

    async def validate_manifest_version(self) -> bool:
        """Validate if version in manifest.json matches the latest stable or prerelease.

        Returns
        -------
            bool: `True` if the version is valid, `False` if there is a mismatch.

        """

        def normalize_version(version: str | None) -> str | None:
            return version.lstrip("v") if version else None

        manifest_version = self.manifest_data.get("version")
        latest_version = normalize_version(self.used_ref)

        if manifest_version == latest_version:
            self.log(
                f"✅ Manifest version validated: '{manifest_version}' "
                f"matches release '{latest_version}'"
            )
            return True

        # Mismatch - version is outdated
        self.log(
            f"Manifest version mismatch: '{manifest_version}' "
            f"(manifest) vs '{latest_version}' (release)",
            logging.WARNING,
        )
        return False

    async def fetch_metadata(self, github: GitHubAPI) -> dict | None:  # noqa: PLR0911
        """Fetch and update the plugin's metadata.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            dict | None: The plugin's metadata if successful,
                if None plugin will be skipped.

        """
        try:
            repo_fetched = await self.fetch_repository_info(github)
            if not repo_fetched:
                self.log("Skipping due to missing repository data.", logging.ERROR)
                return None

            # Check if the repository is archived
            if self.repo_metadata.archived:
                self.log(
                    "Repository is archived. Skipping metadata generation.",
                    logging.WARNING,
                )
                return {self.repo: {"archived": True}}

            # Check if the repository has been renamed
            full_name = self.repo_metadata.full_name
            if full_name.lower() != self.repo.lower():
                self.log(f"Repository renamed to '{full_name}'", logging.WARNING)
                self.repo = full_name  # Update the repo name

            # Fetch plugin domain and validate repository structure
            if not await self.fetch_github_releases(github):
                return None
            # Fetch plugin domain and validate repository structure
            if not await self.validate_plugin_repository(github):
                return None
            # Fetch manifest file and validate domain
            if not await self.fetch_manifest_file(github):
                return None
            # Validate domain and manifest version
            if not await self.validate_manifest_domain():
                return None
            # Validate manifest version against github releases
            if not await self.validate_manifest_version():
                return None

            self.metadata = {
                "etag_release": self.etag_release,
                "etag_repository": self.etag_repository,
                "last_fetched": datetime.now(UTC).isoformat(),
                "last_updated": self.repo_metadata.updated_at,
                "last_version": self.latest_stable,
                "open_issues": self.repo_metadata.open_issues_count,
                "repository": self.repo,
                "stargazers_count": self.repo_metadata.stargazers_count,
                "watchers_count": self.repo_metadata.watchers_count,
                "forks_count": self.repo_metadata.forks_count,
                "topics": self.repo_metadata.topics,
                "used_ref": self.used_ref,
            }

            # Add releases metadata
            self.metadata = {
                "releases": [
                    {
                        "tag_name": self.releases[0].tag_name,
                        "published_at": self.releases[0].published_at,
                        "prerelease": self.releases[0].prerelease,
                    }
                ],
                **self.metadata,
            }

            # Add prerelease version if available
            if self.latest_prerelease:
                self.metadata["last_prerelease"] = self.latest_prerelease
            self.metadata = dict(sorted(self.metadata.items()))

            # Add manifest-specific metadata
            self.metadata = {
                "manifest": {
                    **{
                        key: value
                        for key, value in self.manifest_data.items()
                        if key not in EXCLUDED_KEYS
                    },
                },
                **self.metadata,
            }
        except GitHubException:
            self.log("An error occurred during metadata generation.", logging.ERROR)
            return None

        self.log("🎉 Metadata successfully generated.")
        return {self.repo_metadata.id: self.metadata}
