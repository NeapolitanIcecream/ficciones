#!/usr/bin/env bash
set -euo pipefail
python3 scorer/scoring_contract.py examples/minimal_task.json examples/minimal_model_output.json
