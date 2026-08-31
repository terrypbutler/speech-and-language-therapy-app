"""Access educator-authored content stored inside portable scenarios."""

from __future__ import annotations

from typing import Any


def opening_line(case: dict[str, Any]) -> str:
    return str(
        case.get("dialogue", {}).get(
            "opening_line", "The client waits to speak with you."
        )
    )


def action_response(case: dict[str, Any], action_id: str) -> str:
    return str(
        case.get("dialogue", {})
        .get("action_responses", {})
        .get(
            action_id,
            "The client acknowledges the action without adding new authored information.",
        )
    )


def action_phrases(case: dict[str, Any]) -> dict[str, list[str]]:
    phrases = case.get("dialogue", {}).get("action_phrases", {})
    return phrases if isinstance(phrases, dict) else {}


def free_text_response(case: dict[str, Any], message_count: int) -> str:
    options = case.get("dialogue", {}).get("fallback_responses", [])
    if not isinstance(options, list) or not options:
        options = ["The client listens and waits for the next clear question."]
    return str(options[message_count % len(options)])


def available_dialogue_facts(
    case: dict[str, Any], state: dict[str, object]
) -> list[str]:
    """Return only authored facts whose deterministic conditions are satisfied."""

    available: list[str] = []
    facts = case.get("dialogue", {}).get("facts", [])
    if not isinstance(facts, list):
        return available
    for item in facts:
        if not isinstance(item, dict) or "fact" not in item:
            continue
        conditions = item.get("when", {})
        if isinstance(conditions, dict) and all(
            state.get(key) == value for key, value in conditions.items()
        ):
            available.append(str(item["fact"]))
    return available


def available_dialogue_fact_records(
    case: dict[str, Any], state: dict[str, object]
) -> list[dict[str, str]]:
    """Return available authored facts with stable IDs for dialogue memory."""

    records: list[dict[str, str]] = []
    facts = case.get("dialogue", {}).get("facts", [])
    if not isinstance(facts, list):
        return records
    for index, item in enumerate(facts):
        if not isinstance(item, dict) or "fact" not in item:
            continue
        conditions = item.get("when", {})
        if isinstance(conditions, dict) and all(
            state.get(key) == value for key, value in conditions.items()
        ):
            records.append(
                {"fact_id": f"fact_{index + 1}", "fact": str(item["fact"])}
            )
    return records
