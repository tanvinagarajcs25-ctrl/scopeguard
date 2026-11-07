
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from backend import memory

from backend.models import (
    AnalyzeRequest,
    FeedbackRequest,
    ChangeOrderRequest
)

from backend.agent import classify_request

app = FastAPI(
    title="ScopeGuard API",
    description="API for detecting and managing project scope creep.",
    version="1.0.0",
)

# Locate the project's data directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    """Read a JSON file from the project's data directory."""
    path = DATA_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_sow():
    """Return the project's Statement of Work."""
    return load_json("sow.json")


@app.get("/health")
def health():
    """Check whether the API is running."""
    return {
        "status": "ok",
        "mode": "memory"
    }


@app.get("/messages")
def get_messages():
    """Return all 20 project messages."""
    messages = load_json("messages.json")

    return {
        "messages": messages
    }


@app.post("/load")
def load_project_data():
    """Load the SOW and historical messages without duplicating memories."""

    try:
        existing = memory.client.list_memories(
            bank_id=memory.BANK_ID,
            limit=1
        )

        # Protect against accidentally loading the dataset twice.
        if existing.total > 0:
            return {
                "status": "already_loaded",
                "bank_id": memory.BANK_ID,
                "existing_memory_units": existing.total
            }

        sow = load_json("sow.json")
        messages = load_json("messages.json")
        test_cases = load_json("test_cases.json")
        decisions = load_json("decisions.json")

        sow_count = memory.load_sow(sow)
        history_count = memory.load_history(
            messages,
            test_cases,
            decisions
        )

        return {
            "status": "ok",
            "loaded": {
                "sow_memories": sow_count,
                "history_messages": history_count
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Data loading failed: {str(error)}"
        )


@app.get("/ledger")
def get_ledger():
    """Return the unpaid extras ledger."""
    return memory.get_ledger()


@app.get("/reflect")
def reflect():
    """Retrieve patterns learned from project memories."""

    try:
        return memory.reflect_patterns()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Reflection failed: {str(error)}"
        )


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    """Save the freelancer's decision about a client request."""

    try:
        info = {
            "message_id": request.message_id or "session",
            "message": request.message,
            "verdict": request.verdict,
            "estimated_hours": request.estimated_hours,
            "estimated_cost_inr": request.estimated_cost_inr,
        }

        retained = memory.retain_feedback(
            info,
            request.decision,
            request.note
        )

        return {
            "status": "ok",
            "retained_now": retained,
            "ledger": memory.get_ledger()
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Feedback failed: {str(error)}"
        )

@app.post("/change-order")
def create_change_order(request: ChangeOrderRequest):
    """Generate a draft change order for additional client work."""

    subject = f"Change Order - {request.message_id or 'Additional Work'}"

    body = f"""
Dear Client,

We have reviewed your additional request:

{request.message}

This request requires work beyond the originally agreed Statement of Work.

Estimated effort: {request.estimated_hours} hours
Estimated additional cost: INR {request.estimated_cost_inr}

Reason:
{request.reason or "This request requires additional work outside the agreed project scope."}

As per our agreement, additional work is billed at INR 1,500 per hour
and requires your written approval before commencement.

Please confirm your approval so that we can proceed.

Regards,
Priya
"""

    return {
        "subject": subject,
        "body": body.strip()
    }

@app.post("/analyze")
def analyze_message(request: AnalyzeRequest):
    """Analyze a client request using the SOW and relevant memories."""

    try:
        # 1. Load the Statement of Work
        sow = get_sow()

        # 2. Retrieve memories if memory is enabled
        if request.memory_on:
            memory_context = memory.recall_context(request.message)
            recalled_memories = memory_context or []
        else:
            memory_context = None
            recalled_memories = []

        # 3. Call Teju's AI agent
        result = classify_request(
            request.message,
            sow,
            memory_context
        )

        # 4. Handle errors from the agent
        if result.get("error"):
            return {
                "message_id": request.message_id,
                "message": request.message,
                "memory_on": request.memory_on,
                "verdict": "grey_area",
                "sow_clause_ids": result.get("sow_clause_ids", []),
                "estimated_hours": result.get("estimated_hours", 0),
                "estimated_cost_inr": result.get("estimated_cost_inr", 0),
                "reasoning": result.get("reasoning", ""),
                "recalled_memories": recalled_memories,
                "evidence": [],
                "creep": None,
                "error": result["error"]
            }

        # 5. Calculate scope creep without changing the ledger
        creep = None

        if request.memory_on:
            ledger = memory.get_ledger()

            count = ledger["count"]
            total_cost = ledger["total_cost_inr"]

            existing_ids = {
                item.get("message_id")
                for item in ledger["items"]
            }

            if (
                result["verdict"] == "out_of_scope"
                and request.message_id not in existing_ids
            ):
                count += 1
                total_cost += result.get("estimated_cost_inr", 0)

            creep = {
                "count": count,
                "total_cost_inr": total_cost
            }

        # 6. Return the analysis
        return {
            "message_id": request.message_id,
            "message": request.message,
            "memory_on": request.memory_on,
            "verdict": result["verdict"],
            "sow_clause_ids": result.get("sow_clause_ids", []),
            "estimated_hours": result.get("estimated_hours", 0),
            "estimated_cost_inr": result.get("estimated_cost_inr", 0),
            "reasoning": result.get("reasoning", ""),
            "recalled_memories": recalled_memories,
            "evidence": result.get("evidence", []),
            "creep": creep,
            "error": None
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(error)}"
        )

@app.post("/reset")
def reset_memory_bank():
    """Reset the Hindsight bank when explicitly authorized."""

    try:
        memory.reset_bank()

        return {
            "status": "ok",
            "message": "Memory bank reset successfully."
        }

    except RuntimeError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Bank reset failed: {str(error)}"
        )