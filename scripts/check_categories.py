"""Check if a repository is in categories.json."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Logging setup (GitHub Actions compatible)
logging.addLevelName(logging.INFO, "")
logging.addLevelName(logging.ERROR, "::error::")
logging.addLevelName(logging.WARNING, "::warning::")
logging.basicConfig(
    level=logging.INFO,
    format=" %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger(__name__)


def check_repository_in_categories(repo: str, action: str, categories_file: str) -> int:  # noqa: PLR0911
    """Check if a repository is in categories.json.

    Args:
    ----
        repo (str): Repository name in the format 'owner/repo'.
        action (str): Action performed, either 'add' or 'remove'.
        categories_file (str): Path to the categories.json file.

    Returns:
    -------
        int: 0 if the check passes, 1 if it fails.

    """
    try:
        with Path(categories_file).open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        LOGGER.exception(f"Could not find '{categories_file}'. Ensure it exists.")
        return 1
    except json.JSONDecodeError:
        LOGGER.exception(f"Invalid JSON format in '{categories_file}'")
        return 1
    except Exception:
        LOGGER.exception(f"Unexpected error reading '{categories_file}'")
        return 1

    # Flatten all repos from all categories
    repo_count = sum(
        repo in (repos if isinstance(repos, list) else []) for repos in data.values()
    )

    if action == "add":
        if repo_count != 1:
            LOGGER.error(
                f"Repository '{repo}' must appear in exactly one category (found: {repo_count})"  # noqa: E501
            )
            return 1
        LOGGER.info(f"✅ '{repo}' is in exactly one category in categories.json")
    elif action == "remove":
        if repo_count != 0:
            LOGGER.error(
                f"Repository '{repo}' must NOT appear in any category (found: {repo_count})"  # noqa: E501
            )
            return 1
        LOGGER.info(f"✅ '{repo}' is not in any category in categories.json")
    else:
        LOGGER.error(f"Unknown action: '{action}' (should be 'add' or 'remove')")
        return 1
    return 0


def check_categories_plugins_sync(categories_file: str, plugins_file: str) -> int:
    """Check if all repositories in categories.json exist in plugins.json.

    Args:
    ----
        categories_file (str): Path to the categories.json file.
        plugins_file (str): Path to the plugins.json file.

    Returns:
    -------
        int: 0 if all checks pass, 1 if there are errors.

    """
    errors = 0
    try:
        with Path(plugins_file).open(encoding="utf-8") as pf:
            plugins_list = set(json.load(pf))
    except Exception:
        LOGGER.exception("Could not read or parse plugins.json")
        return 1

    try:
        with Path(categories_file).open(encoding="utf-8") as cf:
            categories_data = json.load(cf)
    except Exception:
        LOGGER.exception("Could not read or parse categories.json")
        return 1

    # Flatten all categorized repositories
    categorized_repos = set()
    for repos in categories_data.values():
        if isinstance(repos, list):
            categorized_repos.update(repos)

    # Check if all categorized repositories exist in plugins.json
    for repo in sorted(categorized_repos):
        if repo not in plugins_list:
            LOGGER.error(
                f"Repository '{repo}' in categories.json does not exist in plugins.json!"  # noqa: E501
            )
            errors += 1

    # Check if all plugins in plugins.json are categorized
    for repo in sorted(plugins_list):
        if repo not in categorized_repos:
            LOGGER.warning(
                f"Repository '{repo}' exists in plugins.json but is not assigned to any category."  # noqa: E501
            )

    if errors == 0:
        LOGGER.info("✅ All repositories in categories.json exist in plugins.json.")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate repository category assignment in categories.json."
    )
    parser.add_argument(
        "--categories-file",
        default="categories.json",
        help="Path to categories.json file (default: categories.json)",
    )
    parser.add_argument(
        "--plugins-file",
        default="plugins.json",
        help="Path to plugins.json file (default: plugins.json)",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["add", "remove"],
        help="Action performed: add or remove",
    )

    args = parser.parse_args()

    repo = os.environ.get("REPOSITORY")
    if not repo:
        LOGGER.error("'REPOSITORY' environment variable is not set or empty.")
        sys.exit(1)
    repo = repo.strip()

    error_count = check_repository_in_categories(
        repo, args.action, args.categories_file
    )
    error_count += check_categories_plugins_sync(
        args.categories_file, args.plugins_file
    )
    sys.exit(1 if error_count else 0)
