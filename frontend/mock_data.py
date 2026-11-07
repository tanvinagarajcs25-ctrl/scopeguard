"""Sharma Retail sample inbox, SOW analysis, ledger, and memory data (INR)."""

messages = [
    {
        "id": "msg-001",
        "client": "Sharma Retail",
        "sender": "Priya Sharma",
        "subject": "Add a wishlist to the app",
        "preview": "Could we add a wishlist so shoppers can save products?",
        "body": "Could we add a wishlist so shoppers can save products and come back to them later?",
        "received": "10:42 AM",
    },
    {
        "id": "msg-002",
        "client": "Sharma Retail",
        "sender": "Priya Sharma",
        "subject": "Change the checkout button label",
        "preview": "Please change the checkout button label from Continue to Place order.",
        "body": "Please change the checkout button label from Continue to Place order on the checkout screen.",
        "received": "Yesterday",
    },
    {
        "id": "msg-003",
        "client": "Sharma Retail",
        "sender": "Priya Sharma",
        "subject": "Personalized product recommendations",
        "preview": "Can the home screen show recommendations based on purchase history?",
        "body": "Could the home screen show product recommendations based on each shopper's purchase history? We are not sure if this is included in the app scope.",
        "received": "Yesterday",
    },
]

SOW = {
    "client": "Sharma Retail",
    "project": "E-commerce mobile app",
    "rate_inr_per_hour": 1500,
    "clauses": [
        {"id": "SOW-2.1", "text": "Deliver a customer-facing e-commerce mobile app for iOS and Android."},
        {"id": "SOW-2.2", "text": "Includes product catalogue, product details, cart, and checkout flows."},
        {"id": "SOW-2.3", "text": "Includes account sign-in and order history."},
        {"id": "SOW-4.1", "text": "New features or integrations beyond listed deliverables require a change request."},
    ],
}

ANALYSES = {
    "msg-001": {
        "verdict": "out_of_scope",
        "reasoning": "A wishlist is a new customer feature and is not listed among the agreed catalogue, cart, checkout, account, or order-history deliverables.",
        "sow_clause_ids": ["SOW-2.1", "SOW-2.2", "SOW-4.1"],
        "estimated_hours": 8,
        "estimated_cost_inr": 12000,
        "recalled_memories": ["Sharma Retail extra-work rate: ₹1,500 per hour."],
        "evidence": ["Requested feature: save products to a wishlist", "No wishlist deliverable appears in the SOW."],
        "creep": True,
        "error": None,
    },
    "msg-002": {
        "verdict": "in_scope",
        "reasoning": "This is a small copy change to the existing checkout screen, which is an agreed deliverable.",
        "sow_clause_ids": ["SOW-2.2"],
        "estimated_hours": 0.5,
        "estimated_cost_inr": 0,
        "recalled_memories": [],
        "evidence": ["The requested button is on the checkout screen."],
        "creep": False,
        "error": None,
    },
    "msg-003": {
        "verdict": "grey_area",
        "reasoning": "Recommendations use the product catalogue and purchase history, but the SOW does not define personalized or algorithmic recommendations. Confirm whether this is a simple catalogue view or a new integration before estimating final scope.",
        "sow_clause_ids": ["SOW-2.2", "SOW-2.3", "SOW-4.1"],
        "estimated_hours": 4,
        "estimated_cost_inr": 6000,
        "recalled_memories": ["Sharma Retail extra-work rate: ₹1,500 per hour."],
        "evidence": ["Request depends on purchase history", "No personalization feature is specified in the SOW."],
        "creep": None,
        "error": None,
    },
}

# Keep named fixtures available for consumers that want a verdict-specific sample.
ANALYZE_ON = ANALYSES["msg-001"]
ANALYZE_OFF = ANALYSES["msg-001"]

FEEDBACK = {"success": True, "message": "Decision saved.", "decision": "charge"}

REFLECT = {
    "retained": [
        {"text": "Sharma Retail SOW: e-commerce mobile app for iOS and Android.", "source": "Signed SOW", "date": "Nov 1"},
        {"text": "Product catalogue, product details, cart, checkout, account sign-in, and order history are included.", "source": "Deliverables", "date": "Nov 1"},
    ],
    "recalled": [
        {"text": "Agreed extra-work rate is ₹1,500 per hour.", "source": "Rate card", "date": "Nov 1"},
    ],
    "learned": [
        {"text": "New app features require a written change request before work begins.", "source": "Project decisions", "date": "Nov 3"},
    ],
}

LEDGER = {
    "unpaid_extra_asks": 1,
    "total_value_inr": 12000,
    "currency": "INR",
    "items": [
        {"client": "Sharma Retail", "description": "Wishlist feature", "estimated_hours": 8, "estimated_cost_inr": 12000, "status": "Awaiting approval"},
    ],
}
