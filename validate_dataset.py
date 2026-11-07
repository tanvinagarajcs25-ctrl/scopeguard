import json
import sys
from pathlib import Path
from datetime import date

DATA = Path("data")

# Load all four JSON files
with open(DATA / "sow.json", encoding="utf-8") as f:
    sow = json.load(f)

with open(DATA / "messages.json", encoding="utf-8") as f:
    messages = json.load(f)

with open(DATA / "decisions.json", encoding="utf-8") as f:
    decisions = json.load(f)

with open(DATA / "test_cases.json", encoding="utf-8") as f:
    tests = json.load(f)

errors = []

def check(condition, message):
    if not condition:
        errors.append(message)

# 1. Check message counts and IDs
check(len(messages) == 20, "Expected 20 messages")
check([m["id"] for m in messages] ==
      [f"msg-{i:03d}" for i in range(1, 21)],
      "Message IDs must be msg-001 to msg-020")

check(sum(m["split"] == "history" for m in messages) == 14,
      "Expected 14 history messages")
check(sum(m["split"] == "heldout" for m in messages) == 6,
      "Expected 6 heldout messages")

message_map = {m["id"]: m for m in messages}
clause_ids = {c["id"] for c in sow["clauses"]}
# 1A. Check SOW details
check(sow["client"] == "Sharma Retail",
      "Incorrect client name")

check(sow["freelancer"] == "Priya",
      "Incorrect freelancer name")

check(sow["project"] == "E-commerce mobile app",
      "Incorrect project name")

check(sow["price_inr"] == 300000,
      "Incorrect contract price")

check(sow["duration_weeks"] == 8,
      "Incorrect project duration")

check(sow["start_date"] == "2026-09-14",
      "Incorrect project start date")

check(sow["extra_work_rate_inr_per_hour"] == 1500,
      "Incorrect extra work rate")

check(sow["revision_rounds_included"] == 2,
      "Incorrect revision rounds")

check(len(sow["clauses"]) == 10,
      "Expected 10 SOW clauses")

check(len(sow["exclusions"]) == 2,
      "Expected 2 SOW exclusions")

check(len(clause_ids) == len(sow["clauses"]),
      "Duplicate SOW clause IDs")

# 2. Check decisions
check(len(decisions) == 8, "Expected 8 decisions")

for d in decisions:
    mid = d["message_id"]
    check(mid in message_map, f"Unknown decision message: {mid}")

    if mid in message_map:
        msg = message_map[mid]
        check(msg["split"] == "history",
              f"Decision references heldout message: {mid}")

        try:
            days = (date.fromisoformat(d["date"]) -
                    date.fromisoformat(msg["date"])).days
            check(0 <= days <= 5,
                  f"Decision date invalid for {mid}")
            check(d["date"] <= "2026-10-15",
                  f"Decision after deadline: {mid}")
        except ValueError:
            errors.append(f"Invalid date in decision: {mid}")

    check(d["decision"] in ["charge", "waive", "edit"],
          f"Invalid decision type: {mid}")

# 3. Check test cases
check(len(tests) == 20, "Expected 20 test cases")

test_ids = [t["message_id"] for t in tests]
check(len(set(test_ids)) == 20,
      "Duplicate test case message IDs")
check(set(test_ids) == set(message_map),
      "Every message must have exactly one test case")

counts = {
    "in_scope": 0,
    "out_of_scope": 0,
    "grey_area": 0
}

for t in tests:
    mid = t["message_id"]

    if mid not in message_map:
        errors.append(f"Unknown test case message: {mid}")
        continue

    verdict = t["verdict"]
    check(verdict in counts, f"Invalid verdict: {mid}")

    if verdict in counts:
        counts[verdict] += 1

    hours = t["estimated_hours"]
    cost = t["estimated_cost_inr"]

    check(isinstance(hours, (int, float)) and
          not isinstance(hours, bool),
          f"Hours must be numeric: {mid}")

    if isinstance(hours, (int, float)) and not isinstance(hours, bool):
        check(hours >= 0, f"Negative hours: {mid}")

        if verdict == "in_scope":
            check(hours == 0, f"In-scope hours must be zero: {mid}")
        else:
            check(hours > 0, f"Out-of-scope/grey hours must be positive: {mid}")
            check(hours * 2 == int(hours * 2),
                  f"Hours must use 0.5 increments: {mid}")

        check(cost == hours * 1500,
              f"Incorrect estimated cost: {mid}")

    check(isinstance(cost, int) and not isinstance(cost, bool),
          f"Cost must be an integer: {mid}")

    clause_list = t["sow_clause_ids"]

    check(all(c in clause_ids for c in clause_list),
          f"Unknown SOW clause ID: {mid}")

    if verdict == "in_scope":
        check(len(clause_list) >= 1,
              f"In-scope case needs a clause: {mid}")

    elif verdict == "grey_area":
        check(len(clause_list) >= 1,
              f"Grey-area case needs an ambiguous clause: {mid}")

    elif verdict == "out_of_scope":
        check(clause_list == [],
              f"Out-of-scope clause list must be empty: {mid}")

    # Check earlier related messages only
    current_num = int(mid[-3:])

    for related in t["related_message_ids"]:
        check(related in message_map,
              f"Unknown related message in {mid}: {related}")

        if related in message_map:
            related_num = int(related[-3:])
            check(related_num < current_num,
                  f"Related message is not earlier: {mid} -> {related}")

check(counts == {
    "in_scope": 8,
    "out_of_scope": 6,
    "grey_area": 6
}, f"Incorrect verdict counts: {counts}")

# 4. Final report
print("\nSCOPEGUARD DATASET VALIDATION")
print("-----------------------------")
print("Messages:", len(messages))
print("Decisions:", len(decisions))
print("Test cases:", len(tests))
print("Verdict counts:", counts)

if errors:
    print("\nVALIDATION FAILED")
    for error in errors:
        print("-", error)

    sys.exit(1)
else:
    print("\nALL CHECKS PASSED!")
    sys.exit(0)
