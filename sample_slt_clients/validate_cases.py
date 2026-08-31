"""Validate the bundled fallback scenario library."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.scenario_repository import load_scenario_library  # noqa: E402


if __name__ == "__main__":
    cases = load_scenario_library(ROOT / "sample_slt_clients" / "client_cases.json")
    print(f"Validated {len(cases)} portable synthetic Studio scenarios.")
