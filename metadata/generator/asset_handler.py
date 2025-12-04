"""Asset handling functionality for GitHub release assets."""

import hashlib
import logging
from typing import TYPE_CHECKING, Any

import aiohttp

if TYPE_CHECKING:
    from aiogithubapi import GitHubAPI

    from .log_buffer import PluginLogBuffer


async def get_release_asset_info(
    github: "GitHubAPI",
    release: Any,
    asset_name: str,
    logger: "PluginLogBuffer",
) -> dict[str, Any] | None:
    """Return comprehensive info for the release asset matching asset_name.

    Args:
    ----
        github: GitHubAPI instance
        release: Release object containing assets
        asset_name: Name of the asset to find
        logger: PluginLogBuffer instance for logging

    Returns:
    -------
        dict[str, Any] | None: Asset information dictionary or None if not found

    """
    asset = next(
        (
            asset
            for asset in getattr(release, "assets", [])
            if getattr(asset, "name", None) == asset_name
        ),
        None,
    )
    if not asset:
        logger.log(
            logging.WARNING,
            f"ℹ️  Asset '{asset_name}' not found in release {release.tag_name}",  # noqa: RUF001
        )
        return None

    # Build asset info dictionary
    asset_info: dict[str, Any] = {"name": asset_name}

    # Add size if available
    size = getattr(asset, "size", None)
    if size is not None:
        asset_info["size"] = size

    # Add download count if available
    download_count = getattr(asset, "download_count", None)
    if download_count is not None:
        asset_info["download_count"] = download_count

    # GitHub API returns digest in format "sha256:HASH"
    digest = getattr(asset, "digest", None)
    if digest:
        # Strip the "sha256:" prefix if present
        asset_info["sha256"] = digest.removeprefix("sha256:")
        return asset_info

    # Fallback: download asset and calculate SHA256 if digest not available
    # This is needed for older releases (before June 2025)
    download_url = getattr(asset, "browser_download_url", None) or getattr(
        asset, "url", None
    )
    if not download_url:
        # Return asset info without SHA256 if no download URL
        return asset_info

    # Reuse aiogithubapi's internal session to avoid new connections
    session = getattr(github, "_session", None)
    created_session = False
    if session is None:
        session = aiohttp.ClientSession()
        created_session = True

    sha256 = hashlib.sha256()
    try:
        async with session.get(download_url) as response:
            response.raise_for_status()
            async for chunk in response.content.iter_chunked(1024 * 64):
                sha256.update(chunk)
        asset_info["sha256"] = sha256.hexdigest()
    except Exception:
        logger.log(
            logging.WARNING,
            f"Failed to fetch digest for asset '{asset_name}' "
            f"from release {release.tag_name}",
        )
        # SHA256 will not be added to asset_info on download failure
    finally:
        if created_session:
            await session.close()

    return asset_info
