from __future__ import annotations

from types import SimpleNamespace

from eha.phase2_run import Phase2OpenAIJsonRunner


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(content='{"ok": true}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)


class FakeClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_openai_json_runner_omits_optional_temperature_and_token_cap() -> None:
    runner = Phase2OpenAIJsonRunner.__new__(Phase2OpenAIJsonRunner)
    runner.client = FakeClient()
    runner.response_format = "none"

    content, usage, used_format = runner.complete(
        model="gpt-5",
        messages=[{"role": "user", "content": "Return JSON."}],
        max_output_tokens=None,
        temperature=None,
        schema_name="test_schema",
        schema={"type": "object"},
    )

    kwargs = runner.client.completions.kwargs
    assert content == '{"ok": true}'
    assert usage == {}
    assert used_format == "none"
    assert "temperature" not in kwargs
    assert "max_completion_tokens" not in kwargs
    assert kwargs["model"] == "gpt-5"


def test_openai_json_runner_includes_explicit_invocation_controls() -> None:
    runner = Phase2OpenAIJsonRunner.__new__(Phase2OpenAIJsonRunner)
    runner.client = FakeClient()
    runner.response_format = "json_object"

    runner.complete(
        model="gpt-5.4",
        messages=[{"role": "user", "content": "Return JSON."}],
        max_output_tokens=4096,
        temperature=0.0,
        schema_name="test_schema",
        schema={"type": "object"},
    )

    kwargs = runner.client.completions.kwargs
    assert kwargs["temperature"] == 0.0
    assert kwargs["max_completion_tokens"] == 4096
    assert kwargs["response_format"] == {"type": "json_object"}
