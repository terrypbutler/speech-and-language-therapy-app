from copy import deepcopy
import unittest

from modules.slt_simulation_engine import (
    add_learner_dialogue,
    apply_action,
    case_by_id,
    end_session,
    learner_export,
    load_cases,
    new_session,
)


class SLTSimulationEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases()

    def setUp(self):
        self.case = case_by_id(self.cases, "SLT-001")
        self.original = deepcopy(self.case)
        self.session = new_session(self.case, "Student SLT")

    def test_session_does_not_mutate_case(self):
        self.session["state"]["rapport"] = 10
        self.assertEqual(self.case, self.original)
        self.assertEqual(self.case["initial_state"]["rapport"], 4)

    def test_supported_conversation_prerequisites(self):
        blocked = apply_action(self.case, self.session, "explore_priority")
        self.assertFalse(blocked.applied)
        apply_action(self.case, self.session, "introduce_and_confirm_access")
        apply_action(self.case, self.session, "reduce_communication_pressure")
        apply_action(self.case, self.session, "offer_supported_modalities")
        result = apply_action(self.case, self.session, "explore_priority")
        self.assertTrue(result.applied)
        self.assertTrue(self.session["state"]["priority_identified"])

    def test_dysphagia_path_blocks_plan_before_supervision(self):
        case = case_by_id(self.cases, "SLT-002")
        session = new_session(case)
        result = apply_action(case, session, "communicate_supported_plan")
        self.assertFalse(result.applied)
        self.assertFalse(session["state"]["plan_understood"])

    def test_time_event_fires_once(self):
        for _ in range(4):
            add_learner_dialogue(self.case, self.session, "Hello", minutes=2)
        self.assertIn("communication_fatigue", self.session["resolved_events"])
        cue_count = len(self.session["state"]["revealed_cues"])
        add_learner_dialogue(self.case, self.session, "One more question", minutes=2)
        self.assertEqual(len(self.session["state"]["revealed_cues"]), cue_count)

    def test_learner_export_excludes_internal_and_facilitator_state(self):
        end_session(self.session)
        exported = learner_export(self.case, self.session)
        self.assertNotIn("facilitator_only", exported)
        self.assertNotIn("state", exported)
        self.assertNotIn("resolved_events", exported)
        self.assertEqual(exported["status"], "ended")


if __name__ == "__main__":
    unittest.main()
