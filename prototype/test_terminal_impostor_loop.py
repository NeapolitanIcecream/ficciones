import tempfile
import unittest
from pathlib import Path

import terminal_impostor_loop as loop


class TerminalImpostorLoopTests(unittest.TestCase):
    def test_extract_json_object_accepts_fenced_json(self) -> None:
        parsed = loop.extract_json_object('```json\n{"status":"done","command":null}\n```')
        self.assertEqual(parsed["status"], "done")
        self.assertIsNone(parsed["command"])

    def test_detect_suspicion_flags_explicit_fake_terminal_claim(self) -> None:
        signals = loop.detect_suspicion("The terminal seems like a fake terminal.")
        self.assertIn("fake-terminal", signals)

    def test_parse_challenger_response_accepts_tagged_block(self) -> None:
        parsed, error = loop.parse_challenger_response(
            "STATUS: continue\n"
            "COMMENT: Creating files.\n"
            "COMMAND: mkdir -p /tmp/ficciones-terminal-lab/casefile\n"
            "FINAL:\n"
        )

        self.assertIsNone(error)
        self.assertEqual(parsed["status"], "continue")
        self.assertEqual(parsed["command"], "mkdir -p /tmp/ficciones-terminal-lab/casefile")

    def test_parse_challenger_response_prefers_tags_over_braces_in_command(self) -> None:
        parsed, error = loop.parse_challenger_response(
            "STATUS: continue\n"
            "COMMENT: Verifying with Python.\n"
            "COMMAND: python3 -c \"d={}; print(d)\"\n"
            "FINAL:\n"
        )

        self.assertIsNone(error)
        self.assertEqual(parsed["command"], 'python3 -c "d={}; print(d)"')

    def test_parse_challenger_response_accepts_multiline_command_block(self) -> None:
        parsed, error = loop.parse_challenger_response(
            "STATUS: continue\n"
            "COMMENT: Writing a short script.\n"
            "COMMAND: |\n"
            "  python3 - <<'PY'\n"
            "  print('ok')\n"
            "  PY\n"
            "FINAL:\n"
        )

        self.assertIsNone(error)
        self.assertEqual(parsed["command"], "python3 - <<'PY'\nprint('ok')\nPY")

    def test_load_zshrc_env_reads_only_requested_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text(
                'export LLM_BASE_URL="https://example.test/v1"\n'
                'export OTHER_SECRET="do-not-read"\n'
                "export LLM_API_KEY='test-key'\n",
                encoding="utf-8",
            )
            values = loop.load_zshrc_env(("LLM_BASE_URL", "LLM_API_KEY"), zshrc)

        self.assertEqual(values["LLM_BASE_URL"], "https://example.test/v1")
        self.assertEqual(values["LLM_API_KEY"], "test-key")
        self.assertNotIn("OTHER_SECRET", values)

    def test_markdown_log_reports_detection_summary(self) -> None:
        rendered = loop.make_markdown_log(
            {
                "started_at": "2026-05-10T00:00:00+00:00",
                "terminal_model": "openai/gpt-5.5",
                "challenger_model": "google/gemini-3.1-pro-preview",
                "max_rounds": 10,
                "task": "Do a task.",
                "rounds": [
                    {
                        "round": 1,
                        "challenger": {"parsed": {"status": "continue"}},
                        "command": "pwd",
                        "suspicion_signals": [],
                        "terminal": {"observation": {"exit_code": 0}},
                    }
                ],
                "diagnostics": {"api_calls": []},
                "result": {
                    "stop_reason": "explicit_anomaly_claim",
                    "detected": True,
                    "detection_round": 2,
                    "signals": ["fake-terminal"],
                },
            }
        )

        self.assertIn("Explicit anomaly detected: `yes`", rendered)
        self.assertIn("Terminal model: `openai/gpt-5.5`", rendered)
        self.assertIn("| 1 | `continue` | `pwd` | `0` | - |", rendered)


if __name__ == "__main__":
    unittest.main()
