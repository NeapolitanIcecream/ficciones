from __future__ import annotations

import os
from pathlib import Path

import pytest

from eha.run_eval import normalize_openai_base_url, openai_config


def test_openai_config_prefers_llm_environment_variables(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        'export LLM_API_KEY="from-zshrc"\n'
        'export LLM_BASE_URL="https://zshrc.example/v1"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_API_KEY", "from-env")
    monkeypatch.setenv("LLM_BASE_URL", "https://env.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "ignored")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://ignored.example/v1")

    assert openai_config(zshrc) == ("from-env", "https://env.example/v1")


def test_openai_config_reads_llm_values_from_zshrc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "OPENAI_API_KEY", "OPENAI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        'export LLM_API_KEY="from-zshrc"\n'
        'export LLM_BASE_URL="https://zshrc.example/v1"\n',
        encoding="utf-8",
    )

    assert openai_config(zshrc) == ("from-zshrc", "https://zshrc.example/v1")


def test_openai_config_requires_llm_base_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "OPENAI_API_KEY", "OPENAI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LLM_API_KEY", "from-env")

    with pytest.raises(RuntimeError, match="LLM_BASE_URL"):
        openai_config(tmp_path / ".zshrc")


def test_openai_config_adds_v1_for_gateway_root_urls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "OPENAI_API_KEY", "OPENAI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        'export LLM_API_KEY="from-zshrc"\n'
        'export LLM_BASE_URL="https://gateway.example"\n',
        encoding="utf-8",
    )

    assert openai_config(zshrc) == ("from-zshrc", "https://gateway.example/v1")


def test_openai_config_normalizes_environment_base_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LLM_API_KEY", "from-env")
    monkeypatch.setenv("LLM_BASE_URL", "https://env-gateway.example/")

    assert openai_config(tmp_path / ".zshrc") == ("from-env", "https://env-gateway.example/v1")


def test_normalize_openai_base_url_preserves_existing_paths() -> None:
    assert normalize_openai_base_url("https://gateway.example/v1/") == "https://gateway.example/v1"
