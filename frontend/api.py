"""Small client for ScopeGuard's API, with a delay-backed local mock mode."""

import time
from typing import Any

import requests

import mock_data


DEFAULT_API_URL = "http://localhost:8000"


def _mock(value: Any) -> Any:
    time.sleep(1)
    # Return a fresh value so callers cannot mutate the shared fixtures.
    import copy

    return copy.deepcopy(value)


def _request(method: str, path: str, *, api_url: str, timeout: float = 10, **kwargs: Any) -> Any:
    try:
        response = requests.request(method, f"{api_url.rstrip('/')}{path}", timeout=timeout, **kwargs)
        response.raise_for_status()
        if not response.content:
            return {"success": True}
        return response.json()
    except requests.RequestException as exc:
        return {"error": f"Could not reach ScopeGuard API: {exc}"}
    except ValueError as exc:
        return {"error": f"ScopeGuard API returned invalid JSON: {exc}"}


def health(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock({"status": "ok", "mode": "mock"}) if mock else _request("GET", "/health", api_url=api_url)


def get_messages(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock(mock_data.messages) if mock else _request("GET", "/messages", api_url=api_url)


def analyze(message: Any, *, memory: bool = True, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        return _mock(mock_data.ANALYZE_ON if memory else mock_data.ANALYZE_OFF)
    return _request("POST", "/analyze", api_url=api_url, json={"message": message, "memory": memory})


def send_feedback(message_id: str, decision: str, details: Any = None, *, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        result = _mock(mock_data.FEEDBACK)
        result["decision"] = decision
        return result
    return _request("POST", "/feedback", api_url=api_url, json={"message_id": message_id, "decision": decision, "details": details})


def get_reflect(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock(mock_data.REFLECT) if mock else _request("GET", "/reflect", api_url=api_url)


def get_ledger(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    return _mock(mock_data.LEDGER) if mock else _request("GET", "/ledger", api_url=api_url)


def load_data(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        return _mock({"success": True, "message": "Sample data is ready."})
    return _request("POST", "/load-data", api_url=api_url)


def reset(*, mock: bool = False, api_url: str = DEFAULT_API_URL) -> Any:
    if mock:
        return _mock({"success": True, "message": "Mock session reset."})
    return _request("POST", "/reset", api_url=api_url)
