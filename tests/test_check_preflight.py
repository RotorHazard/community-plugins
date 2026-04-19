"""Tests for scripts/check_preflight.py."""

import importlib.util
import json
import logging
from pathlib import Path
from types import ModuleType

import pytest

TEST_GITHUB_TOKEN = "test-token"  # noqa: S105


def load_script_module() -> ModuleType:
    """Load the check_preflight script as a module for testing."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_preflight.py"
    spec = importlib.util.spec_from_file_location("check_preflight_module", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_async_main_accepts_repository_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A removed+added pair should pass when GitHub resolves it as a rename."""
    module = load_script_module()
    old_repo = "owner/repo-old"
    new_repo = "owner/repo_new"

    (tmp_path / "plugins_old.json").write_text(json.dumps([old_repo]), encoding="utf-8")
    (tmp_path / "plugins.json").write_text(json.dumps([new_repo]), encoding="utf-8")

    async def fake_get_canonical_repo_name(repository: str, token: str) -> str:
        assert token == TEST_GITHUB_TOKEN
        if repository == old_repo:
            return new_repo
        return repository

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", TEST_GITHUB_TOKEN)
    monkeypatch.setattr(module, "get_canonical_repo_name", fake_get_canonical_repo_name)

    with caplog.at_level(logging.INFO):
        await module.async_main()

    assert "Repository renamed" in caplog.text
    assert old_repo in caplog.text
    assert new_repo in caplog.text


@pytest.mark.asyncio
async def test_async_main_rejects_non_rename_add_remove_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A removed+added pair should still fail when it is not a rename."""
    module = load_script_module()
    old_repo = "owner/repo-old"
    new_repo = "owner/brand-new"

    (tmp_path / "plugins_old.json").write_text(json.dumps([old_repo]), encoding="utf-8")
    (tmp_path / "plugins.json").write_text(json.dumps([new_repo]), encoding="utf-8")

    async def fake_get_canonical_repo_name(repository: str, token: str) -> str:
        assert token == TEST_GITHUB_TOKEN
        return repository

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", TEST_GITHUB_TOKEN)
    monkeypatch.setattr(module, "get_canonical_repo_name", fake_get_canonical_repo_name)

    with pytest.raises(SystemExit) as exc_info:
        await module.async_main()

    assert exc_info.value.code == 1
