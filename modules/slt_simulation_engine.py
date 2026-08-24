"""Deterministic engine for fictional speech and language therapy simulations."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from modules.slt_simulation_content import OPENING_LINES, action_response, free_text_response


DATA_PATH = Path(__file__).resolve().parents[1] / "sample_slt_clients" / "slt_cases.json"


@dataclass(frozen=True)
class ActionResult:
    applied: bool
    message: str
    new_cues: tuple[str, ...] = ()
    fired_events: tuple[str, ...] = ()


def load_cases(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def case_by_id(cases: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for case in cases:
        if case["case_id"] == case_id:
            return case
    raise KeyError(f"Unknown SLT case: {case_id}")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_session(case: dict[str, Any], learner_name: str = "Learner") -> dict[str, Any]:
    state = deepcopy(case["initial_state"])
    state.setdefault("elapsed_minutes", 0)
    state.setdefault("revealed_cues", [])
    return {
        "case_id": case["case_id"],
        "learner_name": learner_name.strip() or "Learner",
        "started_at": _timestamp(),
        "status": "active",
        "state": state,
        "resolved_events": [],
        "transcript": [{
            "role": "client",
            "speaker": case["client"]["display_name"],
            "text": OPENING_LINES.get(case["case_id"], "The client waits to meet you."),
            "minute": 0,
        }],
        "action_log": [],
        "reflection": {},
    }


def _conditions_met(state: dict[str, Any], conditions: dict[str, Any]) -> bool:
    return all(state.get(key) == expected for key, expected in conditions.items())


def _apply_effects(state: dict[str, Any], effects: dict[str, Any]) -> None:
    for key, value in effects.items():
        if key.endswith("_delta"):
            target = key[:-6]
            state[target] = state.get(target, 0) + value
        else:
            state[key] = value
    for bounded in ("rapport", "participation", "communication_load"):
        if bounded in state and isinstance(state[bounded], (int, float)):
            state[bounded] = max(0, min(10, state[bounded]))


def _resolve_due_events(case: dict[str, Any], session: dict[str, Any]) -> tuple[str, ...]:
    fired: list[str] = []
    elapsed = session["state"]["elapsed_minutes"]
    resolved = set(session["resolved_events"])
    for event in case["time_events"]:
        if event["event_id"] in resolved or event["at_minute"] > elapsed:
            continue
        if _conditions_met(session["state"], event["when"]):
            _apply_effects(session["state"], event["effects"])
            cue = event["visible_cue"]
            session["state"]["revealed_cues"].append(cue)
            session["transcript"].append({
                "role": "cue", "speaker": "Visible change", "text": cue, "minute": elapsed
            })
            fired.append(event["event_id"])
        session["resolved_events"].append(event["event_id"])
        resolved.add(event["event_id"])
    return tuple(fired)


def _action(case: dict[str, Any], action_id: str) -> dict[str, Any]:
    for action in case["allowed_actions"]:
        if action["action_id"] == action_id:
            return action
    raise KeyError(f"Unknown action for {case['case_id']}: {action_id}")


def apply_action(case: dict[str, Any], session: dict[str, Any], action_id: str, minutes: int = 2) -> ActionResult:
    if session.get("status") != "active":
        return ActionResult(False, "This simulation has ended. Restart it to continue.")
    action = _action(case, action_id)
    if not _conditions_met(session["state"], action["preconditions"]):
        return ActionResult(False, action.get("blocked_message", "Complete the earlier step first."))
    _apply_effects(session["state"], action["effects"])
    new_cues = tuple(action.get("reveals", []))
    session["state"]["revealed_cues"].extend(new_cues)
    session["state"]["elapsed_minutes"] += max(0, minutes)
    response = action_response(case["case_id"], action_id)
    minute = session["state"]["elapsed_minutes"]
    session["transcript"].extend([
        {"role": "learner_action", "speaker": session["learner_name"], "text": action["label"], "minute": minute},
        {"role": "client", "speaker": case["client"]["display_name"], "text": response, "minute": minute},
    ])
    session["action_log"].append({"action_id": action_id, "label": action["label"], "minute": minute})
    fired = _resolve_due_events(case, session)
    return ActionResult(True, response, new_cues, fired)


def add_learner_dialogue(case: dict[str, Any], session: dict[str, Any], value: str, minutes: int = 1) -> ActionResult:
    clean = " ".join(value.split())[:600]
    if not clean:
        return ActionResult(False, "Enter something to say first.")
    if session.get("status") != "active":
        return ActionResult(False, "This simulation has ended. Restart it to continue.")
    count = sum(item["role"] == "learner_dialogue" for item in session["transcript"])
    session["state"]["elapsed_minutes"] += max(0, minutes)
    minute = session["state"]["elapsed_minutes"]
    reply = free_text_response(case["case_id"], count)
    session["transcript"].extend([
        {"role": "learner_dialogue", "speaker": session["learner_name"], "text": clean, "minute": minute},
        {"role": "client", "speaker": case["client"]["display_name"], "text": reply, "minute": minute},
    ])
    fired = _resolve_due_events(case, session)
    return ActionResult(True, reply, (), fired)


def end_session(session: dict[str, Any]) -> None:
    session["status"] = "ended"
    session["ended_at"] = _timestamp()


def learner_export(case: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"], "case_title": case["title"],
        "synthetic_data_notice": case["synthetic_data_notice"],
        "learner_name": session["learner_name"], "status": session["status"],
        "started_at": session["started_at"], "ended_at": session.get("ended_at"),
        "elapsed_minutes": session["state"]["elapsed_minutes"],
        "transcript": deepcopy(session["transcript"]),
        "actions": deepcopy(session["action_log"]),
        "reflection": deepcopy(session.get("reflection", {})),
    }
