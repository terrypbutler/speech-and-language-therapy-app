from copy import deepcopy
import unittest

from modules.scenario_repository import ScenarioLibraryError, validate_scenario_library
from modules.simulation_engine import load_cases


class ScenarioRepositoryTests(unittest.TestCase):
    def test_bundled_fallback_is_valid_and_portable(self):
        cases = load_cases()
        self.assertEqual(len(cases), 4)
        for case in cases:
            self.assertTrue(case["case_id"].startswith("SLT-"))
            self.assertIn("professional_domains", case["learning"])
            self.assertIn("dialogue", case)
            self.assertGreaterEqual(len(case["educator_rubric"]), 3)

    def test_patient_identifiers_remain_forbidden_in_internal_profile(self):
        case = deepcopy(load_cases()[0])
        case["patient"]["nhs_number"] = "fictional-but-forbidden"
        with self.assertRaises(ScenarioLibraryError):
            validate_scenario_library({"schema_version": "0.2.0", "cases": [case]})

    def test_non_slt_id_is_rejected(self):
        case = deepcopy(load_cases()[0])
        case["case_id"] = "PAT-001"
        with self.assertRaises(ScenarioLibraryError):
            validate_scenario_library({"schema_version": "0.2.0", "cases": [case]})


if __name__ == "__main__":
    unittest.main()
