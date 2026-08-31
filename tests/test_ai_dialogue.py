import unittest

from modules.patient_dialogue import (
    ASSESSMENT_CRITERIA,
    authored_interaction_fallback,
    classify_interaction_intent,
)
from modules.simulation_engine import (
    append_patient_response,
    case_by_id,
    load_cases,
    new_session,
    remove_latest_patient_response,
)


class ClientDialogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = case_by_id(load_cases(), "SLT-001")

    def setUp(self):
        self.session = new_session(self.case)

    def test_assessment_criteria_are_person_centred_and_safety_bounded(self):
        joined = " ".join(ASSESSMENT_CRITERIA).casefold()
        self.assertIn("person-centredness", joined)
        self.assertIn("consent", joined)
        self.assertIn("communication", joined)

    def test_common_conversation_intents_work_for_clients(self):
        self.assertEqual(classify_interaction_intent(self.case, "", "Hello Sam, I am Alex."), "introduction")
        self.assertEqual(classify_interaction_intent(self.case, "", "Thank you, goodbye."), "closing")

    def test_authored_fallback_uses_case_content(self):
        reply, intent = authored_interaction_fallback(
            self.case, self.session,
            "I will offer the communication board",
            "Would pointing or writing help?",
        )
        self.assertTrue(reply)
        self.assertIsNone(intent)

    def test_client_wording_helpers_do_not_change_state(self):
        original = dict(self.session["state"])
        removed = remove_latest_patient_response(self.session)
        self.assertTrue(removed)
        append_patient_response(
            self.case, self.session, "I would like the board, please.",
            nonverbal_cue=self.case["patient"]["nonverbal_palette"][0],
        )
        self.assertEqual(self.session["state"], original)
        self.assertEqual(self.session["transcript"][-1]["role"], "patient")


if __name__ == "__main__":
    unittest.main()
