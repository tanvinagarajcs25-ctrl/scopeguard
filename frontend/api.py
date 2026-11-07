"""ScopeGuard API client with deterministic local mock responses."""

import copy
import time
from typing import Any

import requests

import mock_data

DEFAULT_API_URL = "http://localhost:8000"


def _mock(value: Any) -> Any:
    time.sleep(1)
    return copy.deepcopy(value)


def _request(method: str, path: str, *, api_url: str, timeout: float = 10, **kwargs: Any) -> Any:
    try:
        response = requests.request(method, f"{api_url.rstrip('/')}{path}", timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {"success": True}
    except requests.RequestException as exc:
        return {"error": f"Could not reach ScopeGuard API: {exc}"}
    except ValueError as exc:
        return {"error": f"ScopeGuard API returned invalid JSON: {exc}"}


def health(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock({"status": "ok"}) if mock else _request("GET", "/health", api_url=api_url)


def get_messages(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock(mock_data.messages) if mock else _request("GET", "/messages", api_url=api_url)


def analyze(msg_id: str, text: str, memory_on: bool, *, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        return _mock(mock_data.ANALYSES.get(msg_id, mock_data.ANALYSES["msg-003"]))
    return _request(
        "POST", "/analyze", api_url=api_url,
        json={"message_id": msg_id, "message": text, "memory_on": bool(memory_on)},
    )


def feedback(
    message_id: str,
    message: str,
    verdict: str,
    estimated_hours: float,
    estimated_cost_inr: float,
    decision: str,
    note: str,
    *, mock: bool = False,
    api_url: str = DEFAULT_API_URL,
) -> Any:
    payload = {
        "message_id": message_id,
        "message": message,
        "verdict": verdict,
        "estimated_hours": estimated_hours,
        "estimated_cost_inr": estimated_cost_inr,
        "decision": decision,
        "note": note,
    }
    if mock:
        result = _mock(mock_data.FEEDBACK)
        result["decision"] = decision
        return result
    return _request("POST", "/feedback", api_url=api_url, json=payload)


def send_feedback(message_id: str, decision: str, details: Any = None, *, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    details = details or {}
    return feedback(
        message_id,
        str(details.get("message", "")),
        str(details.get("verdict", "grey_area")),
        float(details.get("estimated_hours", 0) or 0),
        float(details.get("estimated_cost_inr", 0) or 0),
        decision,
        str(details.get("note", "")),
        mock=mock,
        api_url=api_url,
    )


def get_reflect(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock(mock_data.REFLECT) if mock else _request("GET", "/reflect", api_url=api_url)


def get_ledger(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock(mock_data.LEDGER) if mock else _request("GET", "/ledger", api_url=api_url)


def load_data(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        return _mock({"success": True, "message": "Sharma Retail sample data is ready."})
    return _request("POST", "/load", api_url=api_url)


def reset(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        return _mock({"success": True, "message": "Mock session reset."})
    return _request("POST", "/reset", api_url=api_url)
