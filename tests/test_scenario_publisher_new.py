import unittest
from unittest.mock import patch

from modules.scenario_publisher import ScenarioPublishError, publish_scenario
from modules.simulation_engine import case_by_id, load_cases


class ScenarioPublisherTests(unittest.TestCase):
    def test_publish_uses_slt_case_id_and_brand(self):
        case = case_by_id(load_cases(), "SLT-001")
        requests = []

        def fake_request(request, timeout):
            requests.append(request)
            if request.get_method() == "GET":
                return {"sha": "existing"}
            return {"commit": {"html_url": "https://example.invalid/commit"}}

        with patch("modules.scenario_publisher._request_json", side_effect=fake_request):
            url = publish_scenario("owner/slt-library", "main", "token", case)
        self.assertEqual(url, "https://example.invalid/commit")
        self.assertTrue(requests[-1].full_url.endswith("/scenarios/SLT-001.yaml"))
        self.assertEqual(requests[-1].headers["User-agent"], "SLT-Simulation-Studio")

    def test_invalid_repository_is_rejected(self):
        case = case_by_id(load_cases(), "SLT-001")
        with self.assertRaises(ScenarioPublishError):
            publish_scenario("not a repository", "main", "token", case)


if __name__ == "__main__":
    unittest.main()
