# API Availability Check

This check was run after `eha-epistemic-parse-repair` produced zero repaired parses and zero cost.

## Result

The configured `LLM_API_KEY` and `LLM_BASE_URL` are present and model listing works, but OpenAI-provider chat completions are currently blocked at the upstream provider layer.

Tiny JSON smoke calls failed as follows:

| Model | Result |
| --- | --- |
| `openai/gpt-5-mini` | upstream `403` provider Terms of Service error |
| `openai/gpt-5.4-mini` | upstream `403` provider Terms of Service error |
| `openai/gpt-4o-mini` | upstream `403` provider Terms of Service error |
| `~openai/gpt-mini-latest` | upstream `403` provider Terms of Service error |
| `openai/gpt-5-nano` | upstream `403` provider Terms of Service error |
| `openai/gpt-5.4-nano` | upstream `403` provider Terms of Service error |
| `openai/gpt-4.1-mini` | upstream `403` provider Terms of Service error |
| `gpt-5-mini`, `gpt-5.4-mini`, `gpt-4o-mini` | unprefixed model IDs returned `model_not_found` |

## Interpretation

The parse-repair report should be read as an API availability/blockage result, not as evidence that the larger token budget and repair retry failed to improve `gpt-5-mini` output. Repaired metrics remain unavailable until the OpenAI-provider route is usable or the experiment is explicitly rerun with a different, marked repair model.
