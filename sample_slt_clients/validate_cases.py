"""Validate SLT prototype fixtures without third-party dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path


DATA_PATH = Path(__file__).with_name("slt_cases.json")
CASE_ID = re.compile(r"^SLT-\d{3}$")
REQUIRED = {
    "case_id", "title", "synthetic_data_notice", "field", "setting", "client",
    "learning", "scenario", "initial_state", "time_events", "allowed_actions",
    "facilitator_only", "debrief", "safety_contract",
}
FORBIDDEN_IDENTITY_KEYS = {"date_of_birth", "dob", "nhs_number", "address", "postcode", "school_name"}


def validate() -> list[str]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("schema_version") != "0.1.0":
        errors.append("schema_version must be 0.1.0")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a non-empty list"]
    seen: set[str] = set()
    for index, case in enumerate(cases, 1):
        prefix = case.get("case_id", f"case {index}")
        missing = REQUIRED - set(case)
        if missing:
            errors.append(f"{prefix}: missing keys {sorted(missing)}")
        if not CASE_ID.fullmatch(case.get("case_id", "")):
            errors.append(f"{prefix}: invalid case ID")
        if prefix in seen:
            errors.append(f"{prefix}: duplicate case ID")
        seen.add(prefix)
        if case.get("synthetic_data_notice") != "Entirely fictional training case":
            errors.append(f"{prefix}: fictional-data notice is missing")
        forbidden = {key.casefold() for key in case.get("client", {})} & FORBIDDEN_IDENTITY_KEYS
        if forbidden:
            errors.append(f"{prefix}: forbidden identity keys {sorted(forbidden)}")
        action_ids = [item.get("action_id") for item in case.get("allowed_actions", [])]
        if len(action_ids) != len(set(action_ids)):
            errors.append(f"{prefix}: action IDs must be unique")
        if case.get("debrief", {}).get("automatic_competence_decision") is not False:
            errors.append(f"{prefix}: automatic competence decisions must be disabled")
        prohibitions = " ".join(case.get("safety_contract", {}).get("must_not_generate", [])).casefold()
        for concept in ("diagnos", "treatment", "competence"):
            if concept not in prohibitions:
                errors.append(f"{prefix}: safety contract does not mention {concept!r}")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("Validation failed:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("Validated 3 fictional SLT cases with no fixture safety errors.")
