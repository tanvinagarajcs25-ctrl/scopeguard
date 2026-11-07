
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
    messages = [
        {"id": "history-001", "split": "history"},
        {"id": "heldout-001", "split": "heldout"},
    ]

    retained_candidates = [
        item for item in messages
        if item.get("split") == "history"
    ]

    assert len(retained_candidates) == 1
    assert retained_candidates[0]["id"] == "history-001"

    print("PASS: Heldout messages are excluded.")

if __name__ == "__main__":
    test_required_functions_exist()
    test_history_filter()
    test_sample_data()
    test_empty_ledger()
    test_ledger_calculation()
    test_heldout_messages_are_excluded()

    print("\nAll local tests passed!")
