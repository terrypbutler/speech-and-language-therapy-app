"""Turn an educator's plain-language brief into a validated scenario draft."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import re
from typing import Any

from modules import ai_client
from modules.scenario_repository import ScenarioLibraryError, validate_scenario_library


@dataclass(frozen=True)
class AuthoringResult:
    case: dict[str, Any] | None
    error: str = ""


def _clean_json(text: str) -> dict[str, Any]:
    clean = text.strip().replace("```json", "").replace("```", "").strip()
    payload = json.loads(clean)
    if "scenario" in payload and isinstance(payload["scenario"], dict):
        payload = payload["scenario"]
    if not isinstance(payload, dict):
        raise ValueError("AI did not return a scenario object.")
    return payload


def _deep_merge(base: Any, candidate: Any) -> Any:
    """Keep required template structure when a model omits an unchanged field."""

    if not isinstance(base, dict) or not isinstance(candidate, dict):
        return deepcopy(candidate)
    result = deepcopy(base)
    for key, value in candidate.items():
        result[key] = _deep_merge(result[key], value) if key in result else deepcopy(value)
    return result


def _normalise_dialogue_facts(value: Any) -> list[dict[str, Any]]:
    """Accept common model variants while preserving deterministic conditions."""

    if not isinstance(value, list):
        return []
    facts: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            conditions: dict[str, Any] = {}
        elif isinstance(item, dict):
            text = str(item.get("fact") or item.get("text") or item.get("content") or "").strip()
            raw_conditions = item.get("when", item.get("condition", {}))
            conditions = raw_conditions if isinstance(raw_conditions, dict) else {}
        else:
            continue
        if text:
            facts.append({"fact": text, "when": conditions})
    return facts


def _normalise_prescribed_items(value: Any) -> list[dict[str, str]]:
    """Remove generated dose fields and enforce the educator-controlled source."""

    if not isinstance(value, list):
        return []
    items: list[dict[str, str]] = []
    dose_pattern = re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|micrograms?|grams?|g|ml|units?)\b",
        flags=re.IGNORECASE,
    )
    for index, item in enumerate(value, start=1):
        if isinstance(item, dict):
            order_id = str(item.get("order_id") or f"SIM-ORDER-{index:02d}").strip()
            display_text = str(
                item.get("display_text")
                or item.get("description")
                or item.get("name")
                or "Educator-approved simulated prescription item"
            ).strip()
        elif isinstance(item, str):
            order_id = f"SIM-ORDER-{index:02d}"
            display_text = item.strip()
        else:
            continue
        if not display_text or dose_pattern.search(display_text):
            display_text = "Educator-approved simulated prescription item"
        items.append(
            {
                "order_id": order_id,
                "display_text": display_text,
                "dose_source": "Read only from the simulated prescription chart",
            }
        )
    return items


def _invariants(candidate: dict[str, Any], base: dict[str, Any], case_id: str) -> dict[str, Any]:
    result = _deep_merge(base, candidate)
    result["case_id"] = case_id
    result["synthetic_data_notice"] = "Entirely fictional training case"
    result["field"] = "speech and language therapy"
    result["publication_status"] = base.get("publication_status", "development")
    result["scenario_version"] = base.get("scenario_version", "1.0.0")
    result["review"] = deepcopy(base.get("review", {}))
    result.setdefault("debrief", {})["automatic_competence_decision"] = False
    dialogue = result.setdefault("dialogue", {})
    dialogue["facts"] = _normalise_dialogue_facts(dialogue.get("facts", []))
    clinical = result.setdefault("clinical", {})
    clinical["prescribed_items"] = []
    return result


def _prompt(base: dict[str, Any], request: str, case_id: str) -> str:
    return """You are helping an educator author one entirely fictional speech and language therapy simulation.

Transform the educator's ordinary-language request into a complete scenario JSON object. Use the supplied scenario as the exact structural template: preserve every top-level section and all required nested shapes, but adapt the educational content to the request. Return the scenario object only as valid JSON.

Authoring rules:
- This is a development draft, not clinical guidance or an approved curriculum.
- Never include real client data or direct identifiers.
- Never provide diagnoses, assessment scores, food/fluid recommendations, treatment programmes or prognoses. Keep clinical.prescribed_items empty.
- Communication, participation, safety, consent, assent and client-experience changes must be deterministic effects under allowed_actions or time_events.
- Every allowed action needs a matching dialogue.action_responses entry and dialogue.action_phrases list.
- Use clear snake_case IDs. Preconditions and effects must refer to keys in initial_state.
- ai_contract.allowed_state_keys must contain only keys in initial_state.
- AI must be prohibited from generating new observations or assessment findings, diagnoses, treatment recommendations or effects, consent and competence judgements.
- Include at least three educator rubric criteria. Do not make a competence decision.
- Keep the case focused enough for a 10-25 minute supervised rehearsal.

Required case ID: """ + case_id + """

EDUCATOR REQUEST:
""" + request + """

STRUCTURAL TEMPLATE JSON:
""" + json.dumps(base, ensure_ascii=False)


def _generate(model: Any, prompt: str) -> dict[str, Any]:
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return _clean_json(getattr(response, "text", ""))


def generate_scenario_draft(
    base: dict[str, Any],
    request: str,
    case_id: str,
    *,
    model: Any = None,
) -> AuthoringResult:
    """Generate, harden and validate a draft, with one automatic repair attempt."""

    request = " ".join(request.split())[:6000]
    if len(request) < 30:
        return AuthoringResult(None, "Describe the scenario in a little more detail first.")
    active_model = model or ai_client.GenerativeModel(ai_client.AUTHORING_MODEL)
    prompt = _prompt(base, request, case_id)
    try:
        candidate = _invariants(_generate(active_model, prompt), base, case_id)
        validate_scenario_library({"schema_version": "0.2.0", "cases": [candidate]})
        return AuthoringResult(candidate)
    except Exception as first:
        repair = (
            prompt
            + "\n\nYour previous draft failed validation. Correct the issue and return the complete "
            + f"scenario JSON only. Validation issue: {first}\nPrevious draft:\n"
            + json.dumps(locals().get("candidate", {}), ensure_ascii=False)
        )
        try:
            candidate = _invariants(_generate(active_model, repair), base, case_id)
            validate_scenario_library({"schema_version": "0.2.0", "cases": [candidate]})
            return AuthoringResult(candidate)
        except Exception as second:
            return AuthoringResult(None, f"AI could not produce a valid draft yet: {second}")
