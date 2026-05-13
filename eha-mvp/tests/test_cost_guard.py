from __future__ import annotations

import pytest

from eha.cost_guard import BudgetExceeded, CostGuard, cost_for_usage, estimate_tokens


def test_cost_for_usage_uses_model_specific_rates() -> None:
    assert cost_for_usage("openai/gpt-4o-mini", 1_000_000, 1_000_000) == pytest.approx(0.75)
    assert cost_for_usage("gpt-5", 1_000_000, 1_000_000) == pytest.approx(11.25)
    assert cost_for_usage("gpt-5-mini", 1_000_000, 1_000_000) == pytest.approx(2.25)
    assert cost_for_usage("heuristic-sim", 1_000_000, 1_000_000) == 0.0


def test_cost_guard_stops_before_hard_cap() -> None:
    guard = CostGuard(hard_cap_usd=0.0001)

    with pytest.raises(BudgetExceeded):
        guard.before_call("gpt-5.5", "x" * 1000, max_output_tokens=10_000)


def test_estimate_tokens_is_nonzero() -> None:
    assert estimate_tokens("") == 1
