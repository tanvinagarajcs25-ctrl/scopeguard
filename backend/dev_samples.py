
"""Small local dataset for testing ScopeGuard's memory module.

These are development samples, not the final project dataset.
"""

SAMPLE_SOW = {
    "client": "Sharma Retail",
    "freelancer": "Priya",
    "project": "E-commerce mobile app",
    "signed_date": "2026-08-31",
    "start_date": "2026-09-07",
    "duration_weeks": 8,
    "price_inr": 300000,
    "extra_work_rate_inr_per_hour": 1500,
    "revision_rounds_included": 2,
    "milestones": [
        {"name": "Catalogue demo", "date": "2026-09-18"},
        {"name": "Checkout demo", "date": "2026-10-02"},
        {"name": "Beta release", "date": "2026-10-16"},
        {"name": "Final delivery", "date": "2026-11-02"},
    ],
    "clauses": [
        {
            "id": "SOW-1",
            "title": "Project scope",
            "text": "The project covers the agreed e-commerce mobile app features."
        },
        {
            "id": "SOW-2",
            "title": "Extra work",
            "text": "Work outside the agreed scope is billed at Rs 1,500 per hour."
        },
        {
            "id": "SOW-3",
            "title": "Revisions",
            "text": "Two rounds of design revisions are included."
        },
    ],
    "exclusions": [
        "Wishlist feature",
        "Coupon code feature",
        "Loyalty points feature",
    ],
}

SAMPLE_MESSAGES = [
    {
        "id": "msg-001",
        "date": "2026-09-10",
        "sender": "Client",
        "channel": "email",
        "text": "Can we add a wishlist feature to the app?",
        "split": "history",
    },
    {
        "id": "msg-002",
        "date": "2026-09-12",
        "sender": "Priya",
        "channel": "email",
        "text": "The wishlist feature is outside the signed scope.",
        "split": "history",
    },
    {
        "id": "msg-003",
        "date": "2026-09-15",
        "sender": "Client",
        "channel": "chat",
        "text": "Could we also add a coupon code feature?",
        "split": "history",
    },
    {
        "id": "msg-004",
        "date": "2026-09-17",
        "sender": "Client",
        "channel": "chat",
        "text": "Please change the banner colour.",
        "split": "history",
    },
    {
        "id": "msg-005",
        "date": "2026-09-18",
        "sender": "Client",
        "channel": "email",
        "text": "Can we have another round of design changes?",
        "split": "history",
    },
]

SAMPLE_TEST_CASES = [
    {
        "message_id": "msg-001",
        "verdict": "out_of_scope",
        "sow_clause_ids": ["SOW-1", "SOW-2"],
        "estimated_hours": 5,
        "estimated_cost_inr": 7500,
        "related_message_ids": [],
        "notes": "Wishlist is excluded from the agreed scope."
    },
    {
        "message_id": "msg-002",
        "verdict": "in_scope",
        "sow_clause_ids": ["SOW-1"],
        "estimated_hours": 0,
        "estimated_cost_inr": 0,
        "related_message_ids": ["msg-001"],
        "notes": "Freelancer explains the scope boundary."
    },
    {
        "message_id": "msg-003",
        "verdict": "out_of_scope",
        "sow_clause_ids": ["SOW-2"],
        "estimated_hours": 4,
        "estimated_cost_inr": 6000,
        "related_message_ids": ["msg-001"],
        "notes": "Coupon codes are not included in the SOW."
    },
    {
        "message_id": "msg-004",
        "verdict": "in_scope",
        "sow_clause_ids": ["SOW-3"],
        "estimated_hours": 0,
        "estimated_cost_inr": 0,
        "related_message_ids": [],
        "notes": "Treat this sample as an included design revision."
    },
    {
        "message_id": "msg-005",
        "verdict": "out_of_scope",
        "sow_clause_ids": ["SOW-3"],
        "estimated_hours": 2,
        "estimated_cost_inr": 3000,
        "related_message_ids": ["msg-004"],
        "notes": "The included revision rounds have been used."
    },
]

SAMPLE_DECISIONS = [
    {
        "message_id": "msg-001",
        "decision": "waive",
        "note": "Priya waived the first extra request as a goodwill gesture.",
        "date": "2026-09-10",
    },
    {
        "message_id": "msg-003",
        "decision": "waive",
        "note": "Priya waived the coupon request as a goodwill gesture.",
        "date": "2026-09-15",
    },
]
