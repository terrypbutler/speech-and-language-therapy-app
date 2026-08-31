from copy import deepcopy
import unittest

from modules.simulation_engine import (
    apply_action, case_by_id, end_session, load_cases, match_action_id,
    new_session, record_nursing_note, student_export,
)


class SimulationEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases()

    def test_library_contains_four_slt_cases(self):
        self.assertEqual([case["case_id"] for case in self.cases], ["SLT-001", "SLT-002", "SLT-003", "SLT-004"])
        self.assertTrue(all(case["field"] == "speech and language therapy" for case in self.cases))

    def test_new_session_does_not_mutate_case(self):
        case = case_by_id(self.cases, "SLT-001")
        original = deepcopy(case)
        session = new_session(case)
        apply_action(case, session, "confirm_access")
        self.assertEqual(case, original)

    def test_supported_conversation_pathway_enforces_prerequisites(self):
        case = case_by_id(self.cases, "SLT-001")
        session = new_session(case)
        self.assertFalse(apply_action(case, session, "explore_priority").applied)
        for action_id in ("confirm_access", "reduce_pressure", "offer_modalities", "check_yes_no", "explore_priority", "verify_meaning", "agree_next_step"):
            self.assertTrue(apply_action(case, session, action_id, minutes=0).applied)
        self.assertTrue(session["state"]["next_step_agreed"])

    def test_dysphagia_plan_is_blocked_until_escalation(self):
        case = case_by_id(self.cases, "SLT-002")
        session = new_session(case)
        self.assertFalse(apply_action(case, session, "teach_back_plan").applied)
        for action_id in ("introduce_and_permission", "clarify_difficulty", "check_wellbeing", "explain_scope", "pause_and_escalate", "teach_back_plan"):
            self.assertTrue(apply_action(case, session, action_id, minutes=0).applied)

    def test_child_case_preserves_assent_and_both_perspectives(self):
        case = case_by_id(self.cases, "SLT-003")
        session = new_session(case)
        self.assertFalse(apply_action(case, session, "shared_summary").applied)
        for action_id in ("welcome_and_assent", "explain_session", "child_led_observation", "gather_parent_view", "gather_child_view", "shared_summary"):
            self.assertTrue(apply_action(case, session, action_id, minutes=0).applied)
        self.assertEqual(session["state"]["consent_state"], "assent_given")

    def test_authored_phrase_matching_is_case_specific(self):
        aphasia = case_by_id(self.cases, "SLT-001")
        voice = case_by_id(self.cases, "SLT-004")
        self.assertEqual(match_action_id(aphasia, "I will offer the communication board"), "offer_modalities")
        self.assertEqual(match_action_id(voice, "I will set a shared goal"), "set_shared_goal")
        self.assertIsNone(match_action_id(voice, "I will offer the communication board"))

    def test_timed_event_fires_once(self):
        case = case_by_id(self.cases, "SLT-001")
        session = new_session(case)
        apply_action(case, session, "confirm_access", minutes=8)
        self.assertEqual(session["resolved_events"], ["communication_fatigue"])
        apply_action(case, session, "confirm_access", minutes=2)
        self.assertEqual(session["resolved_events"], ["communication_fatigue"])

    def test_notes_and_export_are_learner_safe(self):
        case = case_by_id(self.cases, "SLT-004")
        session = new_session(case)
        self.assertTrue(record_nursing_note(case, session, "Aisha identified end-of-day teaching as the priority.", minutes=0).applied)
        end_session(session)
        exported = student_export(case, session)
        self.assertEqual(len(exported["nursing_notes"]), 1)
        self.assertNotIn("facilitator_only", exported)
        self.assertNotIn("ai_contract", exported)


if __name__ == "__main__":
    unittest.main()
