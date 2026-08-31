"""Load and validate portable scenarios from disk or an HTTPS library."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_LOCAL_LIBRARY = (
    Path(__file__).resolve().parents[1] / "sample_slt_clients" / "client_cases.json"
)
MAX_LIBRARY_BYTES = 5 * 1024 * 1024
CASE_ID = re.compile(r"^SLT-\d{3}$")
REQUIRED_CASE_KEYS = {
    "case_id", "scenario_version", "publication_status", "review", "title",
    "synthetic_data_notice", "field", "setting", "patient", "learning",
    "prebrief", "clinical", "clinical_workspace", "initial_state", "time_events",
    "allowed_actions", "ai_contract", "dialogue", "facilitator_only",
    "educator_rubric", "debrief",
}
FORBIDDEN_IDENTITY_KEYS = {
    "date_of_birth", "dob", "nhs_number", "hospital_number", "address", "postcode"
}


class ScenarioLibraryError(ValueError):
    """Raised when scenario content cannot be loaded safely."""


def _read_source(source: Path | str, token: str, timeout: int) -> bytes:
    source_text = str(source)
    if source_text.casefold().startswith(("http://", "https://")):
        if not source_text.casefold().startswith("https://"):
            raise ScenarioLibraryError("Remote scenario libraries must use HTTPS.")
        headers = {"Accept": "application/json", "User-Agent": "SLT-Simulation-Studio"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            with urlopen(Request(source_text, headers=headers), timeout=timeout) as response:
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_LIBRARY_BYTES:
                    raise ScenarioLibraryError("The scenario library is larger than 5 MB.")
                data = response.read(MAX_LIBRARY_BYTES + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ScenarioLibraryError(f"Could not retrieve the scenario library: {exc}") from exc
    else:
        path = Path(source)
        try:
            if path.stat().st_size > MAX_LIBRARY_BYTES:
                raise ScenarioLibraryError("The scenario library is larger than 5 MB.")
            data = path.read_bytes()
        except OSError as exc:
            raise ScenarioLibraryError(f"Could not read the scenario library: {exc}") from exc
    if len(data) > MAX_LIBRARY_BYTES:
        raise ScenarioLibraryError("The scenario library is larger than 5 MB.")
    return data


def _validate_case(case: Any, index: int) -> list[str]:
    if not isinstance(case, dict):
        return [f"case {index} must be an object"]
    case_id = str(case.get("case_id", ""))
    prefix = case_id or f"case {index}"
    errors: list[str] = []
    missing = REQUIRED_CASE_KEYS - set(case)
    if missing:
        errors.append(f"{prefix}: missing keys {sorted(missing)}")
    if not CASE_ID.fullmatch(case_id):
        errors.append(f"{prefix}: invalid case_id")
    if case.get("synthetic_data_notice") != "Entirely fictional training case":
        errors.append(f"{prefix}: fictional-data notice is missing or changed")
    if case.get("publication_status") not in {"development", "approved"}:
        errors.append(f"{prefix}: publication_status must be development or approved")

    patient = case.get("patient", {})
    if not isinstance(patient, dict):
        errors.append(f"{prefix}: client profile must be an object")
        patient = {}
    forbidden = {str(key).casefold() for key in patient} & FORBIDDEN_IDENTITY_KEYS
    if forbidden:
        errors.append(f"{prefix}: direct identity fields are forbidden")
    if not patient.get("nonverbal_palette"):
        errors.append(f"{prefix}: client needs a nonverbal palette")

    for section, keys in {
        "prebrief": ("role", "orientation", "resources", "limitations", "ground_rules"),
        "clinical_workspace": ("handover", "environment", "available_resources", "record_access"),
    }.items():
        value = case.get(section, {})
        if not isinstance(value, dict) or any(key not in value for key in keys):
            errors.append(f"{prefix}: {section} is incomplete")

    actions = case.get("allowed_actions", [])
    if not isinstance(actions, list) or not actions:
        errors.append(f"{prefix}: allowed_actions must be a non-empty list")
        actions = []
    action_ids = [item.get("action_id") for item in actions if isinstance(item, dict)]
    if len(action_ids) != len(actions) or len(action_ids) != len(set(action_ids)):
        errors.append(f"{prefix}: action IDs must exist and be unique")

    dialogue = case.get("dialogue", {})
    if not isinstance(dialogue, dict):
        dialogue = {}
        errors.append(f"{prefix}: dialogue must be an object")
    if not str(dialogue.get("opening_line", "")).strip():
        errors.append(f"{prefix}: dialogue opening_line is required")
    if not dialogue.get("fallback_responses"):
        errors.append(f"{prefix}: dialogue fallback responses are required")
    for key in ("action_responses", "action_phrases"):
        mapping = dialogue.get(key, {})
        if not isinstance(mapping, dict) or set(action_ids) - set(mapping):
            errors.append(f"{prefix}: every action needs {key}")
    facts = dialogue.get("facts", [])
    if not isinstance(facts, list) or any(
        not isinstance(item, dict)
        or not str(item.get("fact", "")).strip()
        or not isinstance(item.get("when", {}), dict)
        for item in facts
    ):
        errors.append(f"{prefix}: dialogue facts are invalid")

    for item in case.get("clinical", {}).get("prescribed_items", []):
        if not isinstance(item, dict) or set(item) != {"order_id", "display_text", "dose_source"}:
            errors.append(f"{prefix}: prescription fixtures may not contain dose fields")
        elif "simulated prescription chart" not in str(item["dose_source"]).casefold():
            errors.append(f"{prefix}: prescription dose source is invalid")

    contract = case.get("ai_contract", {})
    prohibitions = " ".join(str(item) for item in contract.get("must_not_generate", [])).casefold()
    for concept in ("observations", "diagnosis", "treatment", "judgement"):
        if concept not in prohibitions:
            errors.append(f"{prefix}: AI prohibition must mention {concept}")
    unknown = set(contract.get("allowed_state_keys", [])) - set(case.get("initial_state", {}))
    if unknown:
        errors.append(f"{prefix}: AI contract references unknown state keys")
    rubric = case.get("educator_rubric", [])
    rubric_ids = [item.get("criterion_id") for item in rubric if isinstance(item, dict)]
    if len(rubric) < 3 or len(rubric_ids) != len(rubric) or len(rubric_ids) != len(set(rubric_ids)):
        errors.append(f"{prefix}: educator rubric needs at least 3 unique criteria")
    if case.get("debrief", {}).get("automatic_competence_decision") is not False:
        errors.append(f"{prefix}: automatic competence decisions must be disabled")
    return errors


def validate_scenario_library(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema_version") != "0.2.0":
        raise ScenarioLibraryError("The library must use schema_version 0.2.0.")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ScenarioLibraryError("The library must contain at least one case.")
    errors: list[str] = []
    for index, case in enumerate(cases, start=1):
        errors.extend(_validate_case(case, index))
    ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(set(ids)):
        errors.append("case_id values must be unique across the library")
    if errors:
        preview = "; ".join(errors[:8])
        if len(errors) > 8:
            preview += f"; plus {len(errors) - 8} more error(s)"
        raise ScenarioLibraryError(preview)
    return cases


def load_scenario_library(
    source: Path | str = DEFAULT_LOCAL_LIBRARY,
    *,
    token: str = "",
    timeout: int = 10,
) -> list[dict[str, Any]]:
    data = _read_source(source, token.strip(), timeout)
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScenarioLibraryError("The scenario library is not valid UTF-8 JSON.") from exc
    return validate_scenario_library(payload)
