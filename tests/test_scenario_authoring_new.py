import json
import unittest

from modules.scenario_authoring import generate_scenario_draft
from modules.simulation_engine import case_by_id, load_cases


class Response:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, payload):
        self.payload = payload
        self.prompt = ""

    def generate_content(self, prompt, generation_config=None):
        self.prompt = prompt
        return Response(json.dumps(self.payload))


class ScenarioAuthoringTests(unittest.TestCase):
    def test_generated_draft_is_hardened_for_slt(self):
        base = case_by_id(load_cases(), "SLT-001")
        candidate = {
            "case_id": "WRONG",
            "field": "adult nursing",
            "clinical": {"prescribed_items": [{"name": "unsafe generated medicine"}]},
            "dialogue": {"facts": ["The client wants more time."]},
        }
        model = FakeModel(candidate)
        result = generate_scenario_draft(
            base,
            "Create a fictional supported-conversation rehearsal with a different participation priority.",
            "SLT-005",
            model=model,
        )
        self.assertEqual(result.error, "")
        self.assertEqual(result.case["case_id"], "SLT-005")
        self.assertEqual(result.case["field"], "speech and language therapy")
        self.assertEqual(result.case["clinical"]["prescribed_items"], [])
        self.assertIn("speech and language therapy", model.prompt.casefold())

    def test_too_short_a_brief_is_rejected(self):
        base = case_by_id(load_cases(), "SLT-001")
        result = generate_scenario_draft(base, "Too short", "SLT-005", model=FakeModel({}))
        self.assertIsNone(result.case)


if __name__ == "__main__":
    unittest.main()
