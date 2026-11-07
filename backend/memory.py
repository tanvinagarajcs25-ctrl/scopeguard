# All Hindsight memory operations

"""
ScopeGuard Memory Module
Connects ScopeGuard to Hindsight for long-term project memory.
"""

import os
import re
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from hindsight_client import Hindsight


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

# Load the .env file from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("HINDSIGHT_API_KEY")
BASE_URL = os.getenv("HINDSIGHT_BASE_URL")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "scopeguard-main")

ALLOW_BANK_RESET = (
    os.getenv("SCOPEGUARD_ALLOW_BANK_RESET", "false").lower()
    == "true"
)

# Create one Hindsight client and reuse it.
client = (
    Hindsight(base_url=BASE_URL, api_key=API_KEY)
    if API_KEY and BASE_URL
    else None
)

# Local state used for the unpaid-extra ledger and reflection cache.
_history_ledger = []
_session_feedback = []
_reflection_cache = None


def _get_client():
    """Return the configured Hindsight client."""
    if client is None:
        raise RuntimeError(
            "Hindsight credentials are missing. Check your root .env file."
        )
    return client


def _retain(text, date=None):
    """Store one tagged memory in Hindsight."""
    timestamp = date or datetime.now(timezone.utc).isoformat()

    return _get_client().retain(
        bank_id=BANK_ID,
        content=text,
        timestamp=timestamp,
    )


# --------------------------------------------------
# 2. LOAD THE STATEMENT OF WORK
# --------------------------------------------------

def load_sow(sow: dict) -> int:
    """
    Store the SOW summary and individual clauses.

    Returns the number of memories stored.
    """
    sow_date = sow.get("start_date")

    # Store important commercial terms together.
    summary = (
        f"[SOW] {sow_date or 'Date not specified'} | "
        f"Project: {sow.get('project', 'Not specified')}. "
        f"Client: {sow.get('client', 'Not specified')}. "
        f"Freelancer: {sow.get('freelancer', 'Not specified')}. "
        f"Project price: Rs {sow.get('price_inr', 0)}. "
        f"Extra work rate: Rs "
        f"{sow.get('extra_work_rate_inr_per_hour', 0)} per hour. "
        f"Included revision rounds: "
        f"{sow.get('revision_rounds_included', 0)}. "
        f"Exclusions: {', '.join(sow.get('exclusions', []))}."
    )

    _retain(summary, sow_date)

    count = 1

    # Store each SOW clause separately for easier retrieval.
    for clause in sow.get("clauses", []):
        text = (
            f"[SOW] {sow_date or 'Date not specified'} | "
            f"Clause ID: {clause.get('id')}. "
            f"Title: {clause.get('title')}. "
            f"Details: {clause.get('text')}."
        )

        _retain(text, sow_date)
        count += 1

    print(f"Stored {count} SOW memories.")
    return count


# --------------------------------------------------
# 3. LOAD HISTORICAL MESSAGES
# --------------------------------------------------

def load_history(messages, test_cases, decisions) -> int:
    """
    Store history messages only.

    Heldout messages and their labels are never retained.
    Each history message becomes one memory.
    """
    global _history_ledger

    test_case_map = {
        item["message_id"]: item
        for item in test_cases
    }

    decision_map = {
        item["message_id"]: item
        for item in decisions
    }

    _history_ledger = []
    count = 0

    for message in messages:

        # Important: never load heldout messages.
        if message.get("split") != "history":
            continue

        message_id = message.get("id")
        test_case = test_case_map.get(message_id, {})
        decision = decision_map.get(message_id, {})

        date = message.get("date")
        text = (
            f"[MSG] {date} | "
            f"Message ID: {message_id}. "
            f"Sender: {message.get('sender')}. "
            f"Channel: {message.get('channel')}. "
            f"Message: {message.get('text')}. "
            f"Assessment: {test_case.get('verdict', 'unknown')}. "
            f"Estimated hours: {test_case.get('estimated_hours', 0)}. "
            f"Estimated cost: Rs "
            f"{test_case.get('estimated_cost_inr', 0)}. "
            f"Related messages: "
            f"{', '.join(test_case.get('related_message_ids', []))}. "
            f"Assessment notes: {test_case.get('notes', 'None')}. "
            f"Decision: {decision.get('decision', 'not recorded')}. "
            f"Decision note: {decision.get('note', 'None')}."
        )

        _retain(text, date)
        count += 1

        # Keep ledger information locally.
        if test_case.get("verdict") == "out_of_scope":
            _history_ledger.append({
                "message_id": message_id,
                "date": date,
                "summary": message.get("text", ""),
                "hours": test_case.get("estimated_hours", 0),
                "cost_inr": test_case.get("estimated_cost_inr", 0),
                "decision": decision.get("decision", "not recorded"),
            })

    print(f"Stored {count} historical messages.")
    return count


# --------------------------------------------------
# 4. RECALL RELEVANT MEMORIES
# --------------------------------------------------


def recall_context(message: str, k: int = 8) -> list[dict]:
    """
    Recall relevant memories using two queries.
    Interleave results so SOW context is not pushed out by message matches.
    Deduplicate and classify the returned memories.
    """
    hindsight = _get_client()

    queries = [
        message,
        (
            "What does the signed Statement of Work say about "
            "extra work charges, hourly rates, included revision "
            "rounds and project exclusions?"
        ),
    ]

    results_by_query = []

    for query in queries:
        response = hindsight.recall(
            bank_id=BANK_ID,
            query=query,
        )

        query_results = []

        for item in response.results:
            text = getattr(item, "text", "")
            if text:
                query_results.append(text)

        results_by_query.append(query_results)

    # Interleave results from both queries.
    combined = []
    seen = set()
    max_length = max(
        (len(items) for items in results_by_query),
        default=0,
    )

    for index in range(max_length):
        for query_results in results_by_query:
            if index >= len(query_results):
                continue

            text = query_results[index]
            normalized = " ".join(text.lower().split())

            if normalized in seen:
                continue

            seen.add(normalized)
            combined.append(text)

    recalled = []

    for text in combined:
        lower = text.lower()

        # Hindsight may normalize the original text and remove tags.
        # Infer the memory type from the returned content.
        if (
            "waived" in lower
            or "freelancer decision" in lower
            or "decision note" in lower
        ):
            memory_type = "decision"

        elif (
            "statement of work" in lower
            or "extra work rate" in lower
            or "billed at" in lower
            or "project excludes" in lower
            or "revision rounds included" in lower
            or "included revision rounds" in lower
            or "sow clause" in lower
        ):
            memory_type = "sow"

        else:
            memory_type = "message"

        date_match = re.search(
            r"\b\d{4}-\d{2}-\d{2}\b",
            text,
        )

        date = date_match.group(0) if date_match else None

        recalled.append({
            "text": text,
            "date": date,
            "type": memory_type,
        })

    return recalled[:k]


# --------------------------------------------------
# 5. RETAIN USER FEEDBACK
# --------------------------------------------------

def retain_feedback(info: dict, decision: str, note: str) -> list[str]:
    """
    Retain a new message and the freelancer's decision.

    Returns both stored text strings.
    """
    global _reflection_cache

    if decision not in ("charge", "waive"):
        raise ValueError("Decision must be 'charge' or 'waive'.")

    date = info.get("date") or datetime.now(
        timezone.utc
    ).date().isoformat()

    message_text = (
        f"[MSG] {date} | "
        f"Message ID: {info.get('message_id', 'session')}. "
        f"Message: {info.get('message', '')}. "
        f"Verdict: {info.get('verdict', 'unknown')}. "
        f"Estimated hours: {info.get('estimated_hours', 0)}. "
        f"Estimated cost: Rs {info.get('estimated_cost_inr', 0)}. "
        f"Freelancer decision: {decision}."
    )

    decision_text = (
        f"[DECISION] {date} | "
        f"Message ID: {info.get('message_id', 'session')}. "
        f"Decision: {decision}. "
        f"Reason: {note}."
    )

    _retain(message_text, date)
    _retain(decision_text, date)

    # Feedback changes the patterns, so clear the cached reflection.
    _reflection_cache = None

    # Keep session feedback for the ledger.
    if decision == "waive":
        _session_feedback.append({
            "message_id": info.get("message_id", "session"),
            "date": date,
            "summary": info.get("message", ""),
            "hours": info.get("estimated_hours", 0),
            "cost_inr": info.get("estimated_cost_inr", 0),
            "decision": "waive",
        })

    print("Feedback retained successfully.")
    return [message_text, decision_text]


# --------------------------------------------------
# 6. REFLECT ON CLIENT AND FREELANCER PATTERNS
# --------------------------------------------------

def reflect_patterns() -> dict:
    """Ask Hindsight to identify recurring patterns."""
    global _reflection_cache

    if _reflection_cache is not None:
        return _reflection_cache

    hindsight = _get_client()

    client_answer = hindsight.reflect(
        bank_id=BANK_ID,
        query="What patterns do you see in how this client asks for extra work?",
    )

    policy_answer = hindsight.reflect(
        bank_id=BANK_ID,
        query="What is Priya's policy on charging versus waiving extra work?",
    )

    _reflection_cache = {
        "client_patterns": client_answer.text,
        "freelancer_policy": policy_answer.text,
    }

    return _reflection_cache


# --------------------------------------------------
# 7. RESET THE MEMORY BANK
# --------------------------------------------------

def reset_bank() -> None:
    """
    Delete and recreate the configured ScopeGuard bank.

    WARNING: This permanently deletes memories in that bank.
    """
    if not ALLOW_BANK_RESET:
        raise RuntimeError(
            "Bank reset disabled. Set SCOPEGUARD_ALLOW_BANK_RESET=true "
            "only when intentionally resetting the development bank."
        )
    if BANK_ID != "scopeguard-main":
        raise RuntimeError(
            "Reset blocked: unexpected Hindsight bank ID."
        )

    hindsight = _get_client()

    print(f"Deleting Hindsight bank: {BANK_ID}")
    hindsight.delete_bank(bank_id=BANK_ID)

    print(f"Recreating Hindsight bank: {BANK_ID}")
    hindsight.create_bank(
        bank_id=BANK_ID,
        name="ScopeGuard Main",
    )

    global _history_ledger, _session_feedback, _reflection_cache

    _history_ledger = []
    _session_feedback = []
    _reflection_cache = None

    print("ScopeGuard memory bank reset successfully.")


# --------------------------------------------------
# 8. UNPAID EXTRA-WORK LEDGER
# --------------------------------------------------

def get_ledger() -> dict:
    """
    Return out-of-scope work that was waived or not charged.

    This function uses local Python data only.
    It does not call Hindsight.
    """
    items = []

    # Historical unpaid extras.
    for item in _history_ledger:
        if item["decision"] in ("waive", "not recorded"):
            items.append(item.copy())

    # Feedback from the current session that was waived.
    items.extend(item.copy() for item in _session_feedback)

    total_cost = sum(
        item.get("cost_inr", 0)
        for item in items
    )

    return {
        "count": len(items),
        "total_cost_inr": total_cost,
        "items": items,
    }

def close_client() -> None:
    """Close the shared Hindsight client during application shutdown."""
    if client is not None:
        client.close()
        print("Hindsight client closed.")
