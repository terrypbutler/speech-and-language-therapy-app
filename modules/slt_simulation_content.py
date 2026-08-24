"""Educator-authored dialogue for the SLT concept prototype.

Dialogue adds realism only. State changes remain in the deterministic engine.
"""

from __future__ import annotations


OPENING_LINES: dict[str, str] = {
    "SLT-001": "I know what I want to say... but the word won't come.",
    "SLT-002": "Drinks have been making me cough, but I don't want a fuss.",
    "SLT-003": "Mum says we're here to talk about school. Can I draw while we talk?",
}


ACTION_RESPONSES: dict[str, dict[str, str]] = {
    "SLT-001": {
        "introduce_and_confirm_access": "Sam nods and points to the large-print name card.",
        "reduce_communication_pressure": "Thank you... give me time.",
        "establish_yes_no_reliability": "Sam answers the authored check questions consistently.",
        "offer_supported_modalities": "Sam points to the picture board, then writes the first letter 'g'.",
        "explore_priority": "Garden... I want to tell my daughter about my garden.",
        "summarise_and_verify": "Yes. Garden, daughter, and I need more time.",
        "agree_next_step": "Sam points to 'yes' and keeps the communication board nearby.",
    },
    "SLT-002": {
        "introduce_and_seek_permission": "Yes, we can talk about it.",
        "clarify_reported_difficulty": "It happens mostly with drinks. My voice sounds wet afterwards.",
        "check_immediate_wellbeing": "Jordan is comfortable at rest and follows the conversation.",
        "explain_scope_and_uncertainty": "All right. I understand you need to assess before making a plan.",
        "pause_oral_intake_and_escalate": "Jordan agrees to wait while the supervising clinician is contacted.",
        "communicate_supported_plan": "So I should wait, stay upright, and use the call bell if anything changes.",
        "document_and_handover": "The simulated supervisor receives a concise, factual handover.",
    },
    "SLT-003": {
        "welcome_child_and_parent": "Leah chooses the blue pencil and her mother confirms they are happy to continue.",
        "explain_session_accessibly": "So we talk, play a game, and I can ask for a break.",
        "observe_child_led_interaction": "Leah draws a playground and gives short descriptions when not rushed.",
        "gather_parent_perspective": "Her mother says longer instructions and busy group work are the main difficulties.",
        "check_child_perspective": "When everyone talks fast, I don't know when it's my turn.",
        "offer_processing_support": "Leah answers more fully after the instruction is shortened and repeated once.",
        "summarise_without_diagnosis": "Leah and her mother agree that the summary reflects what they described.",
        "agree_collaborative_next_step": "Leah chooses a movement break before the next activity.",
    },
}


FREE_TEXT_RESPONSES: dict[str, tuple[str, ...]] = {
    "SLT-001": (
        "Sam pauses, gestures, and looks towards the communication board.",
        "Slow... please. One thing.",
    ),
    "SLT-002": (
        "Could you explain what will happen next?",
        "Jordan listens and waits for a clear, short explanation.",
    ),
    "SLT-003": (
        "Can you say that one bit at a time?",
        "Leah looks at her drawing, then back to the learner.",
    ),
}


def action_response(case_id: str, action_id: str) -> str:
    return ACTION_RESPONSES.get(case_id, {}).get(
        action_id, "The client acknowledges the action without adding new information."
    )


def free_text_response(case_id: str, message_count: int) -> str:
    options = FREE_TEXT_RESPONSES.get(
        case_id, ("The client waits for the next clear question.",)
    )
    return options[message_count % len(options)]
