"""Deterministic sample data for running the ScopeGuard UI without the API."""

messages = [
    {
        "id": "msg-001",
        "client": "Northstar Studio",
        "sender": "Maya Chen",
        "subject": "One more section for the launch page?",
        "preview": "Could we add a short FAQ section before Friday's launch?",
        "body": "Could we add a short FAQ section to the launch page before Friday? It would be about six questions. The current page looks great—thanks!",
        "received": "10:42 AM",
        "status": "Needs review",
    },
    {
        "id": "msg-002",
        "client": "Northstar Studio",
        "sender": "Maya Chen",
        "subject": "Re: Homepage design",
        "preview": "The revised hero looks good. Could you also make a mobile variant?",
        "body": "The revised hero looks good. Could you also make a mobile variant? I think that should be a quick change.",
        "received": "Yesterday",
        "status": "Needs review",
    },
    {
        "id": "msg-003",
        "client": "Greenfield Goods",
        "sender": "Jordan Lee",
        "subject": "Invoice and final files",
        "preview": "Payment is sent. Please send over the final brand files.",
        "body": "Payment is sent. Please send over the final brand files when you have a moment.",
        "received": "Yesterday",
        "status": "In scope",
    },
]

ANALYZE_ON = {
    "verdict": "OUT_OF_SCOPE",
    "confidence": 0.94,
    "title": "Likely out of scope",
    "summary": "The signed agreement covers a landing page, but does not include FAQ copy or an FAQ section.",
    "reason": "The request adds a new content section (approximately six questions), beyond the agreed landing-page deliverable.",
    "sow_reference": "Section 2 · Deliverables: one responsive launch landing page with supplied copy.",
    "estimated_hours": 1.5,
    "estimated_value": 180,
    "currency": "USD",
    "suggested_reply": "Happy to add the FAQ section. It falls outside the current landing page scope, so I can send a small change order for approval before I start. Would you like me to do that?",
    "memory_used": True,
    "memory_note": "On the previous extra request, you chose to charge for the additional work.",
}

ANALYZE_OFF = {
    **ANALYZE_ON,
    "memory_used": False,
    "memory_note": None,
}

FEEDBACK = {"success": True, "message": "Decision saved.", "decision": "charge"}

REFLECT = {
    "retained": [
        {"text": "Northstar Studio SOW: one responsive launch landing page using client supplied copy.", "source": "Signed SOW", "date": "Oct 14"},
        {"text": "FAQ writing and additional content sections are not listed as deliverables.", "source": "Scope notes", "date": "Oct 14"},
    ],
    "recalled": [
        {"text": "A similar extra request was charged at $120/hour and approved.", "source": "Decision history", "date": "Oct 28"},
    ],
    "learned": [
        {"text": "For Northstar Studio, you prefer to charge for requests that add new deliverables.", "source": "Your past decisions", "date": "Oct 28"},
    ],
}

LEDGER = {
    "unpaid_extra_asks": 2,
    "total_value": 360,
    "currency": "USD",
    "items": [
        {"client": "Northstar Studio", "description": "FAQ section", "value": 180, "status": "Awaiting approval"},
        {"client": "Northstar Studio", "description": "Mobile hero variant", "value": 180, "status": "Awaiting approval"},
    ],
}
