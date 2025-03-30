"""Check if a plugin repository has published releases."""

import argparse
import asyncio
import logging
import os
import re
import sys

from aiogithubapi import GitHubAPI, GitHubException
from dotenv import load_dotenv

load_dotenv()

REPO_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")

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

        release_count: int = len(response.data)
        LOGGER.info(f"🔍 Found {release_count} release(s) for repository: {repository}")

        if release_count == 0:
            LOGGER.error(f"No releases found for repository: {repository}")
            sys.exit(1)


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
