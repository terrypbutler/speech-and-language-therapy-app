"""Bounded AI variation and deterministic display of fictional adult observations."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from modules import ai_client


CHECK_ORDER = (
    "respiratory_rate",
    "oxygen_saturation",
    "heart_rate",
    "blood_pressure",
    "temperature",
    "alertness",
)

CHECK_ALIASES = {
    "blood_pressure": (r"\bblood pressure\b", r"\bbp\b"),
    "temperature": (r"\btemperature\b", r"\btemp\b"),
    "oxygen_saturation": (
        r"\boxygen saturation\b",
        r"\bblood oxygen\b",
        r"\bspo2\b",
        r"\bsats\b",
    ),
    "heart_rate": (r"\bheart rate\b", r"\bpulse\b"),
    "respiratory_rate": (
        r"\brespiratory rate\b",
        r"\bbreathing rate\b",
        r"\brespirations?\b",
    ),
    "alertness": (r"\balertness\b", r"\bconsciousness\b", r"\bavpu\b"),
}

FULL_SET_PATTERNS = (
    r"\bfull (?:set of )?observations?\b",
    r"\bcomplete (?:set of )?observations?\b",
    r"\btake (?:a |the )?observations?\b",
    r"\bmeasure (?:a |the )?observations?\b",
    r"\bvital signs?\b",
)


@dataclass(frozen=True)
class ObservationGeneration:
    values: dict[str, Any]
    generated: bool
    notice: str = ""


def requested_checks(text: str) -> tuple[str, ...]:
    """Return recognised standard adult observation checks in display order."""

    clean = " ".join(text.casefold().split())
    if any(re.search(pattern, clean) for pattern in FULL_SET_PATTERNS):
        return CHECK_ORDER
    found = {
        check_id
        for check_id, patterns in CHECK_ALIASES.items()
        if any(re.search(pattern, clean) for pattern in patterns)
    }
    return tuple(check_id for check_id in CHECK_ORDER if check_id in found)


def _parse_baseline(case: dict[str, Any]) -> dict[str, Any] | None:
    baseline = case.get("clinical", {}).get("baseline_observations", {})
    required = {
        "respiratory_rate_per_min",
        "oxygen_saturation_percent",
        "oxygen_delivery",
        "heart_rate_per_min",
        "blood_pressure_mmHg",
        "temperature_celsius",
        "alertness",
    }
    if not isinstance(baseline, dict) or not required <= set(baseline):
        return None
    match = re.fullmatch(r"\s*(\d{2,3})\s*/\s*(\d{2,3})\s*", str(baseline["blood_pressure_mmHg"]))
    if not match:
        return None
    try:
        parsed = {
            "respiratory_rate_per_min": int(baseline["respiratory_rate_per_min"]),
            "oxygen_saturation_percent": int(baseline["oxygen_saturation_percent"]),
            "oxygen_delivery": str(baseline["oxygen_delivery"]),
            "heart_rate_per_min": int(baseline["heart_rate_per_min"]),
            "systolic_blood_pressure_mmHg": int(match.group(1)),
            "diastolic_blood_pressure_mmHg": int(match.group(2)),
            "temperature_celsius": float(baseline["temperature_celsius"]),
            "alertness": str(baseline["alertness"]),
        }
        if not (
            4 <= parsed["respiratory_rate_per_min"] <= 60
            and 50 <= parsed["oxygen_saturation_percent"] <= 100
            and 20 <= parsed["heart_rate_per_min"] <= 250
            and 50 <= parsed["systolic_blood_pressure_mmHg"] <= 250
            and 20 <= parsed["diastolic_blood_pressure_mmHg"] <= 150
            and parsed["systolic_blood_pressure_mmHg"]
            > parsed["diastolic_blood_pressure_mmHg"]
            and 25 <= parsed["temperature_celsius"] <= 45
        ):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def _schema(baseline: dict[str, Any]) -> dict[str, Any]:
    alertness_options = list(
        dict.fromkeys(
            [
                baseline["alertness"],
                "alert",
                "new confusion",
                "responds to voice",
                "responds to pain",
                "unresponsive",
            ]
        )
    )
    return {
        "type": "object",
        "properties": {
            "respiratory_rate_per_min": {"type": "integer", "minimum": 4, "maximum": 60},
            "oxygen_saturation_percent": {"type": "integer", "minimum": 50, "maximum": 100},
            "oxygen_delivery": {"type": "string", "enum": [baseline["oxygen_delivery"]]},
            "heart_rate_per_min": {"type": "integer", "minimum": 20, "maximum": 250},
            "systolic_blood_pressure_mmHg": {"type": "integer", "minimum": 50, "maximum": 250},
            "diastolic_blood_pressure_mmHg": {"type": "integer", "minimum": 20, "maximum": 150},
            "temperature_celsius": {"type": "number", "minimum": 25, "maximum": 45},
            "alertness": {"type": "string", "enum": alertness_options},
        },
        "required": [
            "respiratory_rate_per_min",
            "oxygen_saturation_percent",
            "oxygen_delivery",
            "heart_rate_per_min",
            "systolic_blood_pressure_mmHg",
            "diastolic_blood_pressure_mmHg",
            "temperature_celsius",
            "alertness",
        ],
        "additionalProperties": False,
    }


def _within(value: float, anchor: float, tolerance: float) -> bool:
    return anchor - tolerance <= value <= anchor + tolerance


def validate_generated_observations(
    values: dict[str, Any], baseline: dict[str, Any], deterioration_stage: int = 0
) -> dict[str, Any]:
    """Reject implausible or weakly grounded model output and return normalised values."""

    normalised = {
        "respiratory_rate_per_min": int(values["respiratory_rate_per_min"]),
        "oxygen_saturation_percent": int(values["oxygen_saturation_percent"]),
        "oxygen_delivery": str(values["oxygen_delivery"]),
        "heart_rate_per_min": int(values["heart_rate_per_min"]),
        "systolic_blood_pressure_mmHg": int(values["systolic_blood_pressure_mmHg"]),
        "diastolic_blood_pressure_mmHg": int(values["diastolic_blood_pressure_mmHg"]),
        "temperature_celsius": round(float(values["temperature_celsius"]), 1),
        "alertness": str(values["alertness"]),
    }
    allowed_alertness = {
        baseline["alertness"],
        "alert",
        "new confusion",
        "responds to voice",
        "responds to pain",
        "unresponsive",
    }
    if normalised["alertness"] not in allowed_alertness:
        raise ValueError("Generated alertness is not in the bounded vocabulary.")
    stage = max(0, min(2, int(deterioration_stage)))
    tolerances = {
        "respiratory_rate_per_min": 4 + 3 * stage,
        "oxygen_saturation_percent": 3 + 2 * stage,
        "heart_rate_per_min": 15 + 10 * stage,
        "systolic_blood_pressure_mmHg": 20 + 10 * stage,
        "diastolic_blood_pressure_mmHg": 15 + 5 * stage,
        "temperature_celsius": 0.6 + 0.3 * stage,
    }
    for key, tolerance in tolerances.items():
        if not _within(normalised[key], baseline[key], tolerance):
            raise ValueError(f"Generated {key} is too far from the authored baseline.")
    if normalised["oxygen_delivery"] != baseline["oxygen_delivery"]:
        raise ValueError("AI cannot change oxygen delivery.")
    systolic = normalised["systolic_blood_pressure_mmHg"]
    diastolic = normalised["diastolic_blood_pressure_mmHg"]
    if systolic <= diastolic or not 10 <= systolic - diastolic <= 150:
        raise ValueError("Generated blood pressure is internally inconsistent.")
    if stage > 0:
        if normalised["respiratory_rate_per_min"] < baseline["respiratory_rate_per_min"]:
            raise ValueError("Respiratory rate cannot improve during authored deterioration.")
        if normalised["oxygen_saturation_percent"] > baseline["oxygen_saturation_percent"]:
            raise ValueError("Oxygen saturation cannot improve during authored deterioration.")
        if normalised["systolic_blood_pressure_mmHg"] > baseline["systolic_blood_pressure_mmHg"]:
            raise ValueError("Blood pressure cannot improve during authored deterioration.")
        if baseline["alertness"] != "alert" and normalised["alertness"] == "alert":
            raise ValueError("Alertness cannot improve during authored deterioration.")
    return normalised


def _fallback_values(baseline: dict[str, Any]) -> dict[str, Any]:
    return dict(baseline)


def generate_observations(
    case: dict[str, Any],
    session: dict[str, Any],
    model=None,
) -> ObservationGeneration:
    """Generate one stable, bounded fictional set or fall back to the authored baseline."""

    baseline = _parse_baseline(case)
    if baseline is None:
        return ObservationGeneration(
            {},
            False,
            "This scenario has no educator-authored physiological baseline, so no figures were generated.",
        )
    state = session["state"]
    stage = int(state.get("deterioration_stage", 0))
    existing = session.get("generated_observations")
    if (
        isinstance(existing, dict)
        and existing
        and session.get("generated_observation_stage") == stage
    ):
        return ObservationGeneration(dict(existing), True)
    context = {
        "fictional_patient": case["patient"]["display_name"],
        "age": case["patient"]["age"],
        "presenting_context": case["clinical"]["presenting_context"],
        "visible_context": [
            *case["clinical"].get("visible_at_start", []),
            *state.get("revealed_cues", []),
        ],
        "authored_baseline": baseline,
        "deterioration_stage": stage,
    }
    prompt = """Create one coherent set of entirely fictional physical observations for an educator-authored speech and language therapy simulation that explicitly includes a physical-observation baseline. Keep every value close to that baseline and consistent with the visible context. Do not diagnose, recommend treatment, add oxygen, or change alertness without support. If deterioration_stage is above zero, do not improve respiratory rate, oxygen saturation, or systolic blood pressure relative to baseline. Return only the schema-defined JSON.

CONTEXT JSON:
""" + json.dumps(context, ensure_ascii=False)
    try:
        active_model = model or ai_client.GenerativeModel(ai_client.DIALOGUE_MODEL)
        response = active_model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": _schema(baseline),
            },
        )
        raw = getattr(response, "text", "").strip().replace("```json", "").replace("```", "")
        values = validate_generated_observations(
            json.loads(raw), baseline, deterioration_stage=stage
        )
        session["generated_observations"] = dict(values)
        session["generated_observation_stage"] = stage
        return ObservationGeneration(values, True)
    except (Exception, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return ObservationGeneration(
            _fallback_values(baseline),
            False,
            "AI-generated observations failed a safety check; the educator-authored baseline was used.",
        )


def format_observation_results(
    values: dict[str, Any], checks: tuple[str, ...]
) -> str:
    """Format only the observations explicitly requested by the learner."""

    parts: list[str] = []
    for check_id in CHECK_ORDER:
        if check_id not in checks:
            continue
        if check_id == "respiratory_rate":
            parts.append(f"Respiratory rate: {values['respiratory_rate_per_min']} breaths/min")
        elif check_id == "oxygen_saturation":
            parts.append(
                f"Oxygen saturation: {values['oxygen_saturation_percent']}% "
                f"on {values['oxygen_delivery']}"
            )
        elif check_id == "heart_rate":
            parts.append(f"Heart rate: {values['heart_rate_per_min']} beats/min")
        elif check_id == "blood_pressure":
            parts.append(
                "Blood pressure: "
                f"{values['systolic_blood_pressure_mmHg']}/"
                f"{values['diastolic_blood_pressure_mmHg']} mmHg"
            )
        elif check_id == "temperature":
            parts.append(f"Temperature: {values['temperature_celsius']:.1f} °C")
        elif check_id == "alertness":
            parts.append(f"Alertness: {values['alertness']}")
    return "; ".join(parts) + ("." if parts else "")
