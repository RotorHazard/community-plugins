"""Check if a plugin repository has published releases."""

import argparse
import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

from aiogithubapi import GitHubAPI, GitHubException
from dotenv import load_dotenv

load_dotenv()

REPO_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
SEMVER_REGEX = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"  # major.minor.patch
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"  # optional pre-release
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"  # optional build metadata
)

# Loggin setup
logging.addLevelName(logging.INFO, "")
logging.addLevelName(logging.ERROR, "::error::")
logging.addLevelName(logging.WARNING, "::warning::")
logging.basicConfig(
    level=logging.INFO,
    format=" %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger(__name__)


def valid_repository(value: str) -> str:
    """Validate repository format.

    Args:
    ----
        value (str): Repository name.

    """
    if not REPO_REGEX.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid repository format `{value}`. Expected format: 'owner/repo'"  # noqa: EM102
        )
    return value


def is_valid_semver(tag: str) -> bool:
    """Check if a tag follows SemVer format.

    Args:
    ----
        tag (str): Release tag (without the 'v' prefix).

    Returns:
    -------
        bool: True if the tag is valid according to SemVer, otherwise False.

    """
    return bool(SEMVER_REGEX.match(tag))


def select_used_ref(releases: list[Any]) -> str:
    """Select the same release ref used by the metadata generator."""
    sorted_releases = sorted(
        releases, key=lambda release: release.created_at, reverse=True
    )
    latest_stable = next(
        (release for release in sorted_releases if not release.prerelease), None
    )
    selected_release = latest_stable or sorted_releases[0]
    return selected_release.tag_name


def write_github_output(ref: str) -> None:
    """Expose the selected release ref to downstream workflow jobs."""
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path.open(github_output, "a", encoding="utf-8") as output_file:
            print(f"ref={ref}", file=output_file)


async def check_releases(repository: str, token: str) -> None:
    """Check if a GitHub repository has at least one release.

    Args:
    ----
        repository (str): Full repository name, e.g. 'user/repo'.
        token (str): GitHub token.

    """
    async with GitHubAPI(token) as github:
        try:
            response = await github.repos.releases.list(repository)
        except GitHubException:
            LOGGER.exception(f"Failed to fetch releases for repository {repository}.")
            sys.exit(1)

        releases = response.data
        LOGGER.info(f"✅ Found {len(releases)} release(s) for repository: {repository}")

        if len(releases) == 0:
            LOGGER.error(f"No releases found for repository: {repository}")
            sys.exit(1)

        tag = select_used_ref(releases)
        LOGGER.info(f"🔍 Selected release tag: {tag}")

        # Check if the selected release tag follows SemVer
        if not is_valid_semver(tag.removeprefix("v")):
            LOGGER.error(f"The selected release tag '{tag}' does not follow SemVer.")
            sys.exit(1)
        else:
            LOGGER.info("✅ The selected release tag follows SemVer.")
            write_github_output(tag)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check if a GitHub repository has at least one release."
    )
    parser.add_argument(
        "--repository",
        required=True,
        type=valid_repository,
        help="Full repository name, e.g. 'user/repo'.",
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        LOGGER.error(
            "No GitHub token provided. Make sure GITHUB_TOKEN "
            "is set as an environment variable."
        )
        sys.exit(1)

    asyncio.run(check_releases(args.repository, token))
