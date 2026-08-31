"""Publish validated scenario sources to the shared GitHub library."""

from __future__ import annotations

import base64
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from modules.scenario_repository import validate_scenario_library


REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ScenarioPublishError(RuntimeError):
    """Raised when a scenario source cannot be published."""


def _error_detail(exc: HTTPError) -> str:
    try:
        return str(json.loads(exc.read().decode("utf-8")).get("message", exc))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return str(exc)


def _request_json(request: Request, timeout: int) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ScenarioPublishError(f"GitHub rejected the update: {_error_detail(exc)}") from exc
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScenarioPublishError(f"Could not contact GitHub: {exc}") from exc


def _current_sha(url: str, headers: dict[str, str], branch: str, timeout: int) -> str:
    try:
        current = _request_json(
            Request(f"{url}?ref={quote(branch, safe='')}", headers=headers), timeout
        )
    except ScenarioPublishError as exc:
        cause = exc.__cause__
        if isinstance(cause, HTTPError) and cause.code == 404:
            return ""
        raise
    sha = current.get("sha")
    if not isinstance(sha, str) or not sha:
        raise ScenarioPublishError("GitHub did not return the current scenario version.")
    return sha


def publish_scenario(
    repository: str,
    branch: str,
    token: str,
    case: dict[str, Any],
    *,
    scenario_directory: str = "scenarios",
    timeout: int = 15,
) -> str:
    """Create or update one JSON-compatible YAML scenario through GitHub's API."""

    repository = repository.strip()
    branch = branch.strip()
    token = token.strip()
    scenario_directory = scenario_directory.strip().strip("/")
    if not REPOSITORY.fullmatch(repository):
        raise ScenarioPublishError("SCENARIO_GITHUB_REPOSITORY must be owner/repository.")
    if not branch or not token or not scenario_directory:
        raise ScenarioPublishError("GitHub branch, token and scenario directory are required.")

    validate_scenario_library({"schema_version": "0.2.0", "cases": [case]})
    case_id = str(case["case_id"])
    path = f"{scenario_directory}/{case_id}.yaml"
    encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
    url = f"https://api.github.com/repos/{repository}/contents/{encoded_path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "SLT-Simulation-Studio",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    sha = _current_sha(url, headers, branch, timeout)
    raw = json.dumps(case, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    body: dict[str, str] = {
        "message": f"Update scenario {case_id} from SLT Simulation Studio",
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    result = _request_json(
        Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="PUT",
        ),
        timeout,
    )
    return str(result.get("commit", {}).get("html_url", ""))
