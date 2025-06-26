"""Determine repository changes between plugins.json files."""

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


def load_repo_list(path: Path) -> set[str]:
    """Load a JSON list of repositories from file.

    Args:
    ----
        path (Path): Path to the JSON file containing a list of repositories.

    Returns:
    -------
        set[str]: A set of repository names.

    """
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            LOGGER.error(f"{path} is not a JSON list.")
            sys.exit(1)
        return set(data)
    except Exception:
        LOGGER.exception(f"Error reading '{path}'")
        sys.exit(1)


def write_github_output(repository: str, action: str) -> None:
    """Write outputs to GITHUB_OUTPUT for use in workflow."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path.open(github_output, "a", encoding="utf-8") as ghf:
            print(f"repository={repository}", file=ghf)
            print(f"action={action}", file=ghf)


def main() -> None:
    """Check for changes in plugins.json files."""
    old_path = Path("plugins_old.json")
    new_path = Path("plugins.json")

    old_repos = load_repo_list(old_path)
    new_repos = load_repo_list(new_path)

    added = list(new_repos - old_repos)
    removed = list(old_repos - new_repos)

    if len(added) == 1 and len(removed) == 0:
        repo = added[0]
        LOGGER.info(f"✅ One repository added: {repo}")
        write_github_output(repo, "add")
    elif len(added) == 0 and len(removed) == 1:
        repo = removed[0]
        LOGGER.info(f"✅ One repository removed: {repo}")
        write_github_output(repo, "remove")
    elif len(added) == 0 and len(removed) == 0:
        LOGGER.info("No changes to plugins.json detected.")
    else:
        LOGGER.warning("⚠️ PR must add or remove exactly one repository.")
        LOGGER.info(f"Added repositories: {added}")
        LOGGER.info(f"Removed repositories: {removed}")
        LOGGER.info(f"Added count: {len(added)}")
        LOGGER.info(f"Removed count: {len(removed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
