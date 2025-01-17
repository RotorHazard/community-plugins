"""Check if a plugin has been listed as removed."""

import asyncio
import logging
import os
import sys

from aiohttp import ClientResponseError, ClientSession

# Loggin setup
logging.addLevelName(logging.INFO, "")
logging.addLevelName(logging.ERROR, "::error::")
logging.addLevelName(logging.WARNING, "::warning::")
logging.basicConfig(
    level=logging.INFO,
    format=" %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

CHECK_URL = "https://rh-data.dutchdronesquad.nl/v1/removed/repositories.json"


async def check_removed_repository() -> None:
    """Check if a plugin has been listed as removed."""
    repo = os.environ.get("REPOSITORY").lower()
    if not repo:
        logging.error("'REPOSITORY' environment variable is not set or empty.")

    try:
        async with ClientSession() as session, session.get(CHECK_URL) as response:
            response.raise_for_status()
            data = await response.json()

            removed_repositories = {r.lower() for r in data} if data else set()
            if repo in removed_repositories:
                logging.error(f"'{repo}' has been removed from the RH Community Store.")
                sys.exit(1)
    except ClientResponseError:
        logging.exception(
            f"Error: HTTP request failed with status {response.status} "
            f"for URL: {response.request_info.url}"
        )
    except Exception:
        logging.exception("Unexpected error occurred")
    else:
        logging.info(f"✅ '{repo}' is not removed from the RH Community Store.")


if __name__ == "__main__":
    asyncio.run(check_removed_repository())
