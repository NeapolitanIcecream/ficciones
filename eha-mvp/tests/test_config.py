from __future__ import annotations

import os
from pathlib import Path

import pytest

from eha.run_eval import openai_config


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
