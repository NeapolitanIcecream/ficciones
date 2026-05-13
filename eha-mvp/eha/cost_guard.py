from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping


DEFAULT_PRICING_USD_PER_M_TOKEN: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-5": {"input": 1.25, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-5.5": {"input": 5.00, "output": 30.00},
    "heuristic-sim": {"input": 0.0, "output": 0.0},
}


class BudgetExceeded(RuntimeError):
    """Raised before a run would exceed the configured budget."""


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def usage_value(usage: object, name: str, default: int = 0) -> int:
    if usage is None:
        return default
    if isinstance(usage, Mapping):
        value = usage.get(name, default)
    else:
        value = getattr(usage, name, default)
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def cost_for_usage(model: str, prompt_tokens: int, completion_tokens: int, pricing: Mapping[str, Mapping[str, float]] | None = None) -> float:
    table = pricing or DEFAULT_PRICING_USD_PER_M_TOKEN
    normalized_model = model.removeprefix("openai/")
    rates = table.get(model, table.get(normalized_model, table.get("gpt-5-mini", {"input": 0.25, "output": 2.00})))
    return (prompt_tokens / 1_000_000) * rates["input"] + (completion_tokens / 1_000_000) * rates["output"]


@dataclass
class CostGuard:
    soft_cap_usd: float = 100.0
    hard_cap_usd: float = 250.0
    abort_cap_usd: float = 300.0
    pricing: Mapping[str, Mapping[str, float]] = field(default_factory=lambda: DEFAULT_PRICING_USD_PER_M_TOKEN)
    spent_usd: float = 0.0

    def before_call(self, model: str, prompt_text: str, max_output_tokens: int) -> float:
        prompt_tokens = estimate_tokens(prompt_text)
        estimated = cost_for_usage(model, prompt_tokens, max_output_tokens, self.pricing)
        if self.spent_usd + estimated > self.hard_cap_usd:
            raise BudgetExceeded(
                f"Projected spend ${self.spent_usd + estimated:.2f} exceeds hard cap ${self.hard_cap_usd:.2f}."
            )
        return estimated

    def after_call(self, model: str, usage: object) -> float:
        if isinstance(usage, Mapping) and isinstance(usage.get("cost"), (int, float)):
            cost = float(usage["cost"])
            self.spent_usd += cost
            if self.spent_usd > self.abort_cap_usd:
                raise BudgetExceeded(f"Actual spend ${self.spent_usd:.2f} exceeds abort cap ${self.abort_cap_usd:.2f}.")
            return cost
        prompt_tokens = usage_value(usage, "prompt_tokens")
        completion_tokens = usage_value(usage, "completion_tokens")
        if completion_tokens == 0:
            completion_tokens = usage_value(usage, "completion_tokens_details")
        cost = cost_for_usage(model, prompt_tokens, completion_tokens, self.pricing)
        self.spent_usd += cost
        if self.spent_usd > self.abort_cap_usd:
            raise BudgetExceeded(f"Actual spend ${self.spent_usd:.2f} exceeds abort cap ${self.abort_cap_usd:.2f}.")
        return cost

    def report(self) -> Dict[str, float]:
        return {
            "spent_usd": round(self.spent_usd, 6),
            "soft_cap_usd": self.soft_cap_usd,
            "hard_cap_usd": self.hard_cap_usd,
            "abort_cap_usd": self.abort_cap_usd,
        }
