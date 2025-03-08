"""Generate metadata for RH Community plugins."""

import asyncio
import base64
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from aiogithubapi import GitHubAPI, GitHubException, GitHubNotFoundException

# Loggin setup
logging.addLevelName(logging.INFO, "")
logging.addLevelName(logging.ERROR, "::error::")
logging.addLevelName(logging.WARNING, "::warning::")
logging.basicConfig(
    level=logging.INFO,
    format=" %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PLUGIN_LIST_FILE = "plugins.json"
OUTPUT_DIR = "output/plugin"
COMPARE_IGNORE = ["last_fetched", "etag_release", "etag_repository"]

# Create output directories
Path(f"{OUTPUT_DIR}/diff").mkdir(parents=True, exist_ok=True)


class SummaryData:
    """Summary data for metadata generation."""

    def __init__(
        self,
        total: int,
        valid: int,
        archived: int,
        renamed: int,
        skipped: int,
    ) -> None:
        """Initialize the summary data."""
        self.total = total
        self.valid = valid
        self.archived = archived
        self.renamed = renamed
        self.skipped = skipped


class RotorHazardPlugin:
    """Handles fetching metdata for a RotorHazard plugin."""

    def __init__(self, repo: str) -> None:
        """Initialize the plugin."""
        self.repo = repo  # Full repository name (e.g., "owner/repo_name")
        self.domain = None
        self.metadata = {}
        self.manifest_data = {}
        self.repo_data = {}
        self.etag_repository = None
        self.etag_release = None
        self.latest_stable = None
        self.latest_prerelease = None

    async def fetch_repository_info(self, github: GitHubAPI) -> None:
        """Fetch and store repository metadata from GitHub.

        Args:
        ----
            github: GitHubAPI instance.

        """
        try:
            repo_data = await github.repos.get(self.repo)

            self.repo = repo_data.data.full_name
            self.repo_data = repo_data.data
        except GitHubNotFoundException:
            logging.warning(f"<{self.repo}> Repository not found")
        except GitHubException:
            logging.exception(f"<{self.repo}> Error fetching repository info")

    async def fetch_github_releases(self, github: GitHubAPI) -> None:
        """Fetch the latest stable and prerelease versions from GitHub.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            tuple[str | None, str | None]: Latest release and prerelease.

        """
        logging.info(f"<{self.repo}> Fetching releases")
        try:
            releases = await github.repos.releases.list(self.repo)
            if releases.etag:
                self.etag_release = releases.etag

            if not releases.data:
                logging.warning(f"<{self.repo}> No releases found")
                return

            # Ensure releases are sorted by creation date (newest first)
            sorted_releases = sorted(
                releases.data, key=lambda r: r.created_at, reverse=True
            )
            # Extract latest stable and prerelease versions
            self.latest_stable = next(
                (r.tag_name for r in sorted_releases if not r.prerelease), None
            )
            self.latest_prerelease = next(
                (r.tag_name for r in sorted_releases if r.prerelease), None
            )

            logging.info(f"<{self.repo}> Latest stable release: {self.latest_stable}")
            if self.latest_prerelease:
                logging.info(
                    f"<{self.repo}> Latest prerelease: {self.latest_prerelease}"
                )
        except GitHubNotFoundException:
            logging.warning(f"<{self.repo}> Zero github releases found")
        except GitHubException:
            logging.exception(f"<{self.repo}> Error fetching releases")

    async def fetch_manifest_file(self, github: GitHubAPI) -> bool:
        """Fetch the manifest file from the repository.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            bool: True if the manifest file is fetched successfully, False otherwise.

        """
        ref = (
            self.latest_prerelease
            or self.latest_stable
            or self.repo_data.get("default_branch")
        )
        manifest_path = f"custom_plugins/{self.domain}/manifest.json"

        try:
            response = await github.repos.contents.get(
                self.repo, manifest_path, ref=ref
            )
            self.manifest_data = json.loads(
                base64.b64decode(response.data.content).decode("utf-8")
            )

            logging.info(
                f"<{self.repo}> Successfully fetched manifest.json from '{ref}'"
            )
        except GitHubNotFoundException:
            logging.exception(
                f"<{self.repo}> Manifest file not found in '{ref}' branch/release"
            )
        except json.JSONDecodeError:
            logging.exception(f"<{self.repo}> Invalid JSON in manifest file")
        except GitHubException:
            logging.exception(f"<{self.repo}> Error fetching manifest file")
        else:
            return True

    async def validate_plugin_repository(self, github: GitHubAPI) -> str | None:
        """Fetch the plugin domain and validate the repository structure.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            str | None: Plugin domain name.

        """
        try:
            logging.info(f"<{self.repo}> Fetching plugin domain")
            response = await github.repos.contents.get(
                self.repo, etag=self.etag_repository
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
                logging.error(f"<{self.repo}> The `custom_plugins/` folder is missing")
                return None

            # Fetch the contens of the `custom_plugins/` folder
            folder_response = await github.repos.contents.get(
                self.repo, "custom_plugins"
            )
            subfolders = [item for item in folder_response.data if item.type == "dir"]

            # Ensure there is exactly one domain folder
            if len(subfolders) != 1:
                logging.error(
                    f"<{self.repo}> Expected exactly one domain folder inside "
                    f"`custom_plugins/` but found: {len(subfolders)}."
                )
                return None

            # Get the domain folder name
            self.domain = subfolders[0].name
            logging.info(f"<{self.repo}> Found domain '{self.domain}'")
        except GitHubNotFoundException:
            logging.warning(f"<{self.repo}> Repository not found")
        except GitHubException:
            logging.exception(f"<{self.repo}> Error fetching plugin domain")
        else:
            return self.domain

    async def validate_manifest_domain(self) -> bool:
        """Validate that the domain in `manifest.json` matches the folder name.

        Returns
        -------
            bool: True if the domain matches the folder name, False otherwise.

        """
        if not self.domain:
            logging.error(f"<{self.repo}> Domain is not set, cannot validate manifest")
            return False

        if not self.manifest_data:
            logging.error(
                f"<{self.repo}> No manifest data available to validate domain"
            )
            return False

        manifest_domain = self.manifest_data.get("domain")
        # Compare the domain in the manifest with the folder name
        if manifest_domain != self.domain:
            logging.error(
                f"<{self.repo}> Domain mismatch: Folder "
                f"'{self.domain}' vs Manifest '{manifest_domain}'"
            )
            return False

        # Domain matches
        logging.info(
            f"<{self.repo}> Domain validated: '{self.domain}' matches manifest domain."
        )
        return True

    async def validate_manifest_version(
        self,
        last_version: str | None,
        prerelease_version: str | None,
    ) -> bool:
        """Validate if version in manifest.json matches the latest stable or prerelease.

        Args:
        ----
            last_version: Latest stable release tag.
            prerelease_version: Latest prerelease tag.

        Returns:
        -------
            bool: `True` if the version is valid, `False` if there is a mismatch.

        """

        def normalize_version(version: str | None) -> str | None:
            """Remove 'v' prefix from version strings."""
            return version.lstrip("v") if version else None

        logging.info(f"<{self.repo}> Validating manifest version")
        manifest_version = self.manifest_data.get("version")

        if not manifest_version:
            logging.error(f"<{self.repo}> Manifest version is missing")
            return False

        last_version = normalize_version(last_version)
        prerelease_version = normalize_version(prerelease_version)

        # If the version matches either stable or prerelease
        if manifest_version in {last_version, prerelease_version}:
            return True

        # Mismatch - version is outdated
        warning_message = (
            f"<{self.repo}> Version mismatch: '{manifest_version}' "
            f"(manifest) vs '{last_version}' (latest stable)"
        )
        if prerelease_version:
            warning_message += f", '{prerelease_version}' (prerelease)"
        logging.warning(warning_message)
        return False

    async def fetch_metadata(self, github: GitHubAPI) -> dict | str | None:
        """Fetch and update the plugin's metadata.

        Args:
        ----
            github: GitHubAPI instance.

        Returns:
        -------
            dict | str | None: Plugin metadata if successful, "archived" if archived,

        """
        try:
            logging.info(f"<{self.repo}> Fetching repository metadata")
            await self.fetch_repository_info(github)

            # Check if the repository is archived
            if self.repo_data.archived:
                logging.error(f"<{self.repo}> Repository is archived")
                return "archived"

            await self.fetch_github_releases(github)

            # Check if the repository has been renamed
            full_name = self.repo_data.full_name
            if full_name.lower() != self.repo.lower():
                logging.error(
                    f"<{self.repo}> Repository has been renamed to '{full_name}'"
                )
                self.repo = full_name  # Update the repo name

            # Fetch plugin domain and validate repository structure
            if not await self.validate_plugin_repository(github):
                return None

            # Fetch manifest file and validate domain
            if not await self.fetch_manifest_file(github):
                return None

            # Validate domain and manifest
            if not await self.validate_manifest_domain():
                return None

            # Validate manifest version against github releases
            if not await self.validate_manifest_version(
                self.latest_stable, self.latest_prerelease
            ):
                return None

            self.metadata = {
                "etag_release": self.etag_release,
                "etag_repository": self.etag_repository,
                "last_fetched": datetime.now(UTC).isoformat(),
                "last_updated": self.repo_data.updated_at,
                "last_version": self.latest_stable,
                "open_issues": self.repo_data.open_issues_count,
                "repository": self.repo,
                "stargazers_count": self.repo_data.stargazers_count,
                "topics": self.repo_data.topics,
            }

            # Add prerelease version if available
            if self.latest_prerelease:
                self.metadata["last_prerelease"] = self.latest_prerelease
            self.metadata = dict(sorted(self.metadata.items()))

            # Add manifest-specific metadata
            self.metadata = {
                "manifest": {
                    "name": self.manifest_data.get("name"),
                    "description": self.manifest_data.get("description"),
                    "category": self.manifest_data.get("category"),
                    **{
                        key: self.manifest_data[key]
                        for key in ["zip_release", "zip_filename"]
                        if key in self.manifest_data
                    },
                },
                "domain": self.domain,
                **self.metadata,
            }
        except GitHubNotFoundException:
            logging.warning(f"<{self.repo}> Repository not found")
        except GitHubException:
            logging.exception(f"<{self.repo}> Error fetching repository metadata")
        else:
            logging.info(f"<{self.repo}> Metadata successfully generated")
            return {self.repo: self.metadata}


class MetadataGenerator:
    """Handles generating and saving metadata for all repositories."""

    def __init__(self, plugin_file: str, output_dir: str) -> None:
        """Initialize the metadata generator."""
        self.plugin_file = Path(plugin_file)
        self.output_dir = output_dir
        self.repos_list = self.load_repos()

    def load_repos(self) -> list[str]:
        """Load repository list from the plugin file.

        Returns
        -------
            list[str]: List of repositories.

        """
        if self.plugin_file.exists():
            with Path.open(self.plugin_file, encoding="utf-8") as f:
                return json.load(f)
        else:
            logging.warning("Plugin list file not found. Using an empty list.")
            return []

    def save_filtered_json(self, filepath: str, data: dict) -> None:
        """Save data to a JSON file with filtered keys.

        Args:
        ----
            filepath: Path to the output JSON file.
            data: Data to be saved.

        """
        filtered_data = {
            key: {k: v for k, v in value.items() if k not in COMPARE_IGNORE}
            for key, value in data.items()
        }
        with Path.open(filepath, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, indent=2)

    def save_json(self, filepath: str, data: dict) -> None:
        """Save data to a JSON file.

        Args:
        ----
            filepath: Path to the output JSON file.
            data: Data to be saved.

        """
        with Path.open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def summarize_results(
        self,
        summary_data: SummaryData,
        start_time: float,
    ) -> None:
        """Summarize the generation results.

        Args:
        ----
            total: Total number of repositories.
            summary_data: An instance of SummaryData containing summary data.
            start_time: Time when the generation started.

        """
        end_time = perf_counter()
        elapsed_time = end_time - start_time

        summary = {
            "total_plugins": summary_data.total,
            "valid_plugins": summary_data.valid,
            "archived_plugins": summary_data.archived,
            "renamed_plugins": summary_data.renamed,
            "skipped_plugins": summary_data.skipped,
            "execution_time_seconds": round(elapsed_time, 2),
        }
        summary_path = f"{self.output_dir}/summary.json"
        self.save_json(summary_path, summary)

    async def generate_metadata(self) -> None:
        """Generate metadata for all repositories."""
        plugin_data: dict[str, dict] = {}
        valid_repositories: list[str] = []
        skipped_plugins = 0
        archived_plugins = 0
        renamed_plugins = 0

        start_time = perf_counter()

        async with GitHubAPI(token=GITHUB_TOKEN) as github:
            tasks = [
                RotorHazardPlugin(repo).fetch_metadata(github)
                for repo in self.repos_list
            ]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result == "archived":
                    archived_plugins += 1
                elif result:
                    repo_id, metadata = next(iter(result.items()))
                    plugin_data[repo_id] = metadata
                    valid_repositories.append(metadata["repository"])
                    # Check if the repository name was updated
                    if (
                        metadata["repository"]
                        != self.repos_list[
                            valid_repositories.index(metadata["repository"])
                        ]
                    ):
                        renamed_plugins += 1
                else:
                    skipped_plugins += 1

        # Save generated metadata to local JSON file
        self.save_filtered_json(f"{self.output_dir}/diff/after.json", plugin_data)
        self.save_json(f"{self.output_dir}/data.json", plugin_data)
        self.save_json(f"{self.output_dir}/repositories.json", valid_repositories)

        # Summarize the results
        summary_data = SummaryData(
            total=len(self.repos_list),
            valid=len(valid_repositories),
            archived=archived_plugins,
            renamed=renamed_plugins,
            skipped=skipped_plugins,
        )
        await self.summarize_results(summary_data, start_time)


if __name__ == "__main__":
    asyncio.run(MetadataGenerator(PLUGIN_LIST_FILE, OUTPUT_DIR).generate_metadata())
