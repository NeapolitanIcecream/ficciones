from __future__ import annotations

from eha.uncued_contract import contract_payload, write_contract_report


def test_uncued_contract_defines_machine_readable_leakage_boundaries(tmp_path) -> None:
    payload = contract_payload()

    assert payload["preferred_term"] == "role_uncued"
    assert "content_neutral" == payload["avoid_as_main_term"]
    assert "primary" in payload["forbidden_role_phrases"]
    assert "secondary" in payload["forbidden_role_phrases"]
    assert "contaminant" in payload["forbidden_role_phrases"]
    assert "model_call_go_no_go_rule" in payload
    assert "id_only" in payload["baseline_thresholds"]

    write_contract_report(tmp_path)

    assert (tmp_path / "eha_uncued_data_contract.json").exists()
    assert (tmp_path / "eha-uncued-data-contract-2026-05-22.md").exists()
    assert (tmp_path / "uncued_data_contract.md").exists()

