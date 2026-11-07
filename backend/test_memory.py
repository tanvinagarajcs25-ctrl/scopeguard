
"""Local tests for ScopeGuard's memory module.

These tests do not contact Hindsight or consume API credits.
"""

from backend import memory
from backend.dev_samples import (
    SAMPLE_SOW,
    SAMPLE_MESSAGES,
    SAMPLE_TEST_CASES,
    SAMPLE_DECISIONS,
)

import json
from pathlib import Path


def test_required_functions_exist():
    required = [
        "load_sow",
        "load_history",
        "recall_context",
        "retain_feedback",
        "reflect_patterns",
        "reset_bank",
        "get_ledger",
    ]

    for name in required:
        assert callable(getattr(memory, name, None)), (
            f"Missing function: {name}"
        )

    print("PASS: All seven required functions exist.")


def test_history_filter():
    history_messages = [
        message
        for message in SAMPLE_MESSAGES
        if message["split"] == "history"
    ]

    heldout_messages = [
        message
        for message in SAMPLE_MESSAGES
        if message["split"] == "heldout"
    ]

    assert len(history_messages) == 5
    assert len(heldout_messages) == 0

    print("PASS: Sample data contains five history messages and no heldout messages.")


def test_sample_data():
    assert SAMPLE_SOW["extra_work_rate_inr_per_hour"] == 1500
    assert SAMPLE_SOW["revision_rounds_included"] == 2
    assert len(SAMPLE_TEST_CASES) == len(SAMPLE_MESSAGES)
    assert len(SAMPLE_DECISIONS) == 2

    print("PASS: Sample data follows the expected structure.")


def test_empty_ledger():
    # This is a local test. It does not call Hindsight.
    ledger = memory.get_ledger()

    assert isinstance(ledger, dict)
    assert "count" in ledger
    assert "total_cost_inr" in ledger
    assert "items" in ledger

    print("PASS: Ledger has the required fields.")

def test_ledger_calculation():
    old_history = memory._history_ledger
    old_feedback = memory._session_feedback

    try:
        memory._history_ledger = [
            {
                "message_id": "test-001",
                "date": "2026-09-10",
                "summary": "Wishlist feature",
                "hours": 5,
                "cost_inr": 7500,
                "decision": "waive",
            },
            {
                "message_id": "test-002",
                "date": "2026-09-15",
                "summary": "Coupon code feature",
                "hours": 4,
                "cost_inr": 6000,
                "decision": "charge",
            },
            {
                "message_id": "test-003",
                "date": "2026-09-18",
                "summary": "Extra revision",
                "hours": 2,
                "cost_inr": 3000,
                "decision": "not recorded",
            },
        ]

        memory._session_feedback = [
            {
                "message_id": "test-004",
                "date": "2026-10-20",
                "summary": "Loyalty points",
                "hours": 8,
                "cost_inr": 12000,
                "decision": "waive",
            }
        ]

        ledger = memory.get_ledger()

        assert ledger["count"] == 3
        assert ledger["total_cost_inr"] == 22500

        print("PASS: Ledger excludes charged work.")
        print("PASS: Ledger includes waived and unrecorded work.")

    finally:
        memory._history_ledger = old_history
        memory._session_feedback = old_feedback


def test_heldout_messages_are_excluded():
    # Capture retained text without contacting Hindsight.
    original_retain = memory._retain
    captured = []

    def fake_retain(text, date=None):
        captured.append(text)

    test_messages = SAMPLE_MESSAGES + [
        {
            "id": "heldout-001",
            "date": "2026-10-20",
            "sender": "Client",
            "channel": "chat",
            "text": "This heldout message must not be retained.",
            "split": "heldout",
        }
    ]

    try:
        memory._retain = fake_retain

        memory.load_history(
            test_messages,
            SAMPLE_TEST_CASES,
            SAMPLE_DECISIONS,
        )

        assert len(captured) == 5
        assert all("heldout-001" not in text for text in captured)
        assert all(
            "heldout message must not be retained" not in text
            for text in captured
        )

        print("PASS: Actual load_history excludes heldout messages.")

    finally:
        memory._retain = original_retain


def test_real_dataset_integration():
    """Test the actual committed dataset without contacting Hindsight."""

    data_dir = Path(__file__).resolve().parents[1] / "data"

    # Read the four real JSON files.
    with open(data_dir / "sow.json", encoding="utf-8") as f:
        sow = json.load(f)

    with open(data_dir / "messages.json", encoding="utf-8") as f:
        messages = json.load(f)

    with open(data_dir / "decisions.json", encoding="utf-8") as f:
        decisions = json.load(f)

    with open(data_dir / "test_cases.json", encoding="utf-8") as f:
        test_cases = json.load(f)

    # Capture memory instead of calling Hindsight.
    original_retain = memory._retain
    captured = []

    def fake_retain(text, date=None):
        captured.append({"text": text, "date": date})

    try:
        memory._retain = fake_retain

        # Test SOW loading.
        sow_count = memory.load_sow(sow)

        assert sow_count == 11
        assert len(captured) == 11
        assert all(
            item["date"] == "2026-09-14"
            for item in captured
        )

        print("PASS: Actual SOW loaded as 11 memories.")

        # Clear captured SOW memories before testing history.
        captured.clear()

        # Test historical message loading.
        history_count = memory.load_history(
            messages, test_cases, decisions
        )

        assert history_count == 14
        assert len(captured) == 14

        retained_text = "\n".join(
            item["text"] for item in captured
        )

        # Verify heldout messages are excluded.
        heldout = [
            item for item in messages
            if item["split"] == "heldout"
        ]

        assert len(heldout) == 6

        for item in heldout:
            assert item["id"] not in retained_text

        print("PASS: Exactly 14 history messages retained.")
        print("PASS: All 6 heldout messages excluded.")

        # Verify all 8 historical decisions are preserved.
        for decision in decisions:
            assert decision["message_id"] in retained_text
            assert decision["decision"] in retained_text

        print("PASS: All 8 historical decisions preserved.")

        # Specifically verify the edit decision.
        edit_decisions = [
            item for item in decisions
            if item["decision"] == "edit"
        ]

        assert len(edit_decisions) == 1
        assert "Decision: edit" in retained_text

        print("PASS: The edit decision is preserved.")

        # Check the ledger.
        ledger = memory.get_ledger()

        assert isinstance(ledger, dict)
        assert ledger["count"] == 0
        assert ledger["total_cost_inr"] == 0
        assert ledger["items"] == []

        print("PASS: Historical ledger calculation is correct.")

    finally:
        memory._retain = original_retain

if __name__ == "__main__":
    test_required_functions_exist()
    test_history_filter()
    test_sample_data()
    test_empty_ledger()
    test_ledger_calculation()
    test_heldout_messages_are_excluded()
    test_real_dataset_integration()

    print("\nAll local tests passed!")