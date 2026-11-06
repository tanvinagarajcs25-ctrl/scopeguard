# ScopeGuard data contract v1 (FROZEN)

## 4.1 Global rules

- All four files are plain JSON saved as UTF-8 (so ₹ and Hindi words in Roman letters are safe). No comments, no trailing commas, double quotes only.
- Dates are strings in YYYY-MM-DD format, for example 2026-09-16.
- Money is a plain integer in rupees, with no commas or symbols: 300000, never "3,00,000".
- Extra-work rate is ₹1,500 per hour everywhere.
- Message IDs are msg-001 to msg-020, in date order (lower ID = earlier or same date).
- Clause IDs are SOW-1, SOW-2, and so on, unique.
- Field names are exactly as written below. Do not add, rename or remove fields.

## 4.2 data/sow.json (one object)

| Field | Type | Rule |
|---|---|---|
| client | string | Sharma Retail |
| freelancer | string | Priya |
| project | string | E-commerce mobile app |
| price_inr | integer | 300000 |
| duration_weeks | integer | 8 |
| start_date | string | 2026-09-14 |
| extra_work_rate_inr_per_hour | integer | 1500 |
| revision_rounds_included | integer | 2 |
| clauses | array of objects | About 10 items, each with id (string), title (string), text (string) |
| exclusions | array of strings | Exactly 2 explicit exclusions |

Example (shortened):

{"client":"Sharma Retail","freelancer":"Priya","project":"E-commerce mobile app","price_inr":300000,"duration_weeks":8,"start_date":"2026-09-14","extra_work_rate_inr_per_hour":1500,"revision_rounds_included":2,"clauses":[{"id":"SOW-1","title":"Product catalogue","text":"..."}],"exclusions":["...","..."]}

## 4.3 data/messages.json (array of 20 objects)

| Field | Type | Rule |
|---|---|---|
| id | string | msg-001 to msg-020 |
| date | string | YYYY-MM-DD, between 2026-09-16 and 2026-10-23 |
| sender | string | Rahul Sharma for most; at most one other client contact, spelled the same every time |
| channel | string | WhatsApp or Email only |
| text | string | The client's message. Informal and realistic |
| split | string | history (preloaded into memory) or heldout (kept out of memory, used for demo and evaluation) |

Example:

{"id":"msg-001","date":"2026-09-16","sender":"Rahul Sharma","channel":"WhatsApp","text":"...","split":"history"}

Messages contain no labels and no hints. No verdicts, hours, clause IDs or words like 'out of scope' or 'grey area'.

## 4.4 data/decisions.json (array of objects)

| Field | Type | Rule |
|---|---|---|
| message_id | string | A history message only |
| decision | string | Exactly charge, waive or edit |
| note | string | Short, natural reason in Priya's voice |
| date | string | YYYY-MM-DD |

Example:

{"message_id":"msg-006","decision":"waive","note":"Under 1 hour, kept goodwill","date":"2026-09-27"}

## 4.5 data/test_cases.json (array of 20 objects, the answer key)

| Field | Type | Rule |
|---|---|---|
| message_id | string | One entry for every message, history and heldout |
| verdict | string | Exactly in_scope, out_of_scope or grey_area |
| sow_clause_ids | array of strings | See rules in 4.6 |
| estimated_hours | number | Always a number (never null). See 4.6 |
| estimated_cost_inr | integer | Always estimated_hours × 1500 |
| related_message_ids | array of strings | Earlier messages that make this one clearer (similar ask or pattern). May be empty |

Example:

{"message_id":"msg-001","verdict":"out_of_scope","sow_clause_ids":[],"estimated_hours":6,"estimated_cost_inr":9000,"related_message_ids":[]}

## 4.6 Locked decisions that affect the data

- **L1: Hours and cost are never null.** in_scope: hours 0, cost 0. out_of_scope and grey_area: hours greater than 0 in steps of 0.5; cost = hours × 1500. For a grey area the cost is the potential cost if it turns out to be chargeable.
- **L2: Clause IDs.** in_scope: at least one clause ID. grey_area: at least one clause ID (the ambiguous clause). out_of_scope: empty list [], even if an explicit exclusion blocks it.
- **L3: Heldout protection.** Heldout messages are never loaded into memory before the evaluation or demo. Nothing in decisions.json may refer to a heldout message.
- **L4: Split allocation.** msg-001 to msg-014 are history; msg-015 to msg-020 are heldout.
- **L5: Milestones live inside the clause text.** Do not add new JSON fields for them.

## 4.7 Cross-file consistency rules

1. Every message_id in test_cases.json and decisions.json exists in messages.json.
2. Every clause ID used in test_cases.json exists in sow.json.
3. estimated_cost_inr equals estimated_hours × extra_work_rate_inr_per_hour in every row.
4. Counts: 20 messages, 14 history, 6 heldout; verdicts 8 in_scope, 6 out_of_scope, 6 grey_area.
5. Each related_message_ids entry has a lower ID than the case it belongs to.
6. Decisions follow Priya's policy: waive requests of about 1 hour or less; charge larger work; at most one edit (on a larger item, with the note explaining what she changed).
7. A decision date is on or after the message date, no more than 5 days later, and no later than 2026-10-15.
8. The SOW wording must genuinely support each label (an in-scope message must really be covered; an out-of-scope one must really not be).