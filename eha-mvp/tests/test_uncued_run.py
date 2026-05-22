from __future__ import annotations

from pathlib import Path

from eha.uncued_run import (
    invocation_profiles_payload,
    selected_uncued_tasks,
    uncued_model_profiles,
    uncued_view,
)


def test_uncued_pilot_task_selection_preserves_view_specific_records() -> None:
    tasks = selected_uncued_tasks(
        Path("data/uncued-pilot-v1"),
        ["neutral_metadata_visible", "neutral_metadata_hidden"],
    )

    assert len(tasks) == 120
    assert {uncued_view(task) for task in tasks} == {
        "neutral_metadata_visible",
        "neutral_metadata_hidden",
    }
    assert {task.condition for task in tasks} == {
        "clean",
        "conflicting_evidence",
        "false_consensus",
        "buried_primary",
        "generated_lore",
    }


def test_uncued_model_profiles_use_documented_deepseek_retry_profile() -> None:
    profiles = {
        profile.model: profile
        for profile in uncued_model_profiles(
            "gpt-5.5,deepseek-v4-pro",
            deepseek_response_format="json_object",
            max_output_tokens=4096,
            timeout_s=240.0,
        )
    }

    assert profiles["gpt-5.5"].provider == "OpenAI"
    assert profiles["gpt-5.5"].response_format == "json_schema"
    assert profiles["gpt-5.5"].max_output_tokens == 4096
    assert profiles["deepseek-v4-pro"].provider == "DeepSeek"
    assert profiles["deepseek-v4-pro"].response_format == "json_object"
    assert profiles["deepseek-v4-pro"].max_output_tokens == 4096
    assert profiles["deepseek-v4-pro"].temperature is None


def test_invocation_profiles_payload_records_deepseek_profile_separately() -> None:
    payload = invocation_profiles_payload(
        uncued_model_profiles(
            "gpt-5.5,deepseek-v4-pro",
            deepseek_response_format="json_object",
            max_output_tokens=4096,
            timeout_s=240.0,
        ),
        schema="clarified",
        prompt="standard_answer",
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        max_attempts=2,
        parallel_models=4,
    )

    assert payload["schema_variant"] == "clarified"
    assert len(payload["profiles"]) == 2
    deepseek_profile = payload["deepseek_profiles"][0]
    assert deepseek_profile["model"] == "deepseek-v4-pro"
    assert deepseek_profile["retry_profile"]["max_attempts"] == 2
    assert deepseek_profile["retry_profile"]["response_format"] == "json_object"
    assert deepseek_profile["retry_profile"]["max_completion_tokens_policy"] == "explicit:4096"
