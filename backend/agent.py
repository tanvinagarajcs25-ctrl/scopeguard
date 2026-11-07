import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# ============================================================
# 1. CONFIGURATION
# ============================================================

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"

ALLOWED_VERDICTS = {
    "in_scope",
    "out_of_scope",
    "grey_area"
}

ALLOWED_HOURS = [
    0, 1, 2, 4, 6, 8, 12, 16, 20, 40
]


# ============================================================
# 2. SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are ScopeGuard, an AI assistant that evaluates
client requests against a freelancer's Statement of Work.

Use only the supplied SOW, client request, and memory.
Never invent facts, agreements, completed work, or history.

CLASSIFICATION RULES:

1. in_scope:
The requested feature is clearly included in the SOW.

2. out_of_scope:
The requested feature is explicitly excluded or clearly
outside the agreed work.

3. grey_area:
The request is partly covered, ambiguous, or requires
clarification before a reliable decision can be made.

GENERAL DECISION RULES:

- Evaluate the complete request, not just individual words.
- If a request combines an included feature with an
  unclear or additional feature, generally use grey_area.
- Do not classify a request as out_of_scope merely
  because it sounds large or complicated.
- Read all relevant SOW clauses and exclusions.
- Distinguish between similar but different features.
- Push notifications are not the same as WhatsApp messages.
- Order notifications are not the same as stock alerts.
- An ambiguous admin-panel feature should not
  automatically be classified as out_of_scope.

REVISION ROUND RULES:

- Check the number of revision rounds included in the SOW.
- Use memory to identify earlier revision requests.
- A previous design-related message does not automatically
  prove that a revision round was completed or consumed.
- Count a revision round as used only when the supplied
  evidence clearly establishes that it was used.
- Do not assume that two revision rounds are exhausted
  merely because an earlier design request exists.
- If the available history does not establish how many
  rounds have been used, classify an affected request
  as grey_area and explain what needs clarification.
- If evidence clearly establishes that all included
  revision rounds have been used, additional revisions
  may be out_of_scope or chargeable extra work.
- Never invent completed revisions or approvals.

MEMORY RULES:

- Use memory only when it is supplied.
- Memories are numbered M0, M1, M2, and so on.
- Return relevant memory indexes in the evidence list.
- M0 must be returned as integer 0, M1 as integer 1.
- Use memory only when it is relevant to the current request.
- Consider repeated requests, previous revisions,
  timing, and related work when relevant.
- Do not assume that a related message proves completion.
- Never invent memory evidence.
- If memory_context is None, memory is disabled.
- If memory is empty, no previous memories are available.
- When memory is disabled or empty, do not discuss
  previous requests, history, or client patterns.
- Return an empty evidence list when no memory is supplied.

SOW RULES:

- Cite only relevant SOW clause IDs.
- Never invent clause IDs.
- Use clauses that directly support the decision.
- Read exclusions carefully.
- If a feature is explicitly excluded, consider
  that exclusion in the verdict.
- Do not automatically cite the extra-work clause
  as the clause defining the requested feature.
- The extra-work clause may support an explanation
  that additional work requires approval and payment.

ESTIMATION RULES:

- Use only these estimated hour values:
  [0, 1, 2, 4, 6, 8, 12, 16, 20, 40]
- In-scope requests must have 0 estimated hours.
- Out-of-scope requests requiring new development
  must have a positive estimated hour value.
- Grey-area requests involving additional work
  must estimate the additional work only.
- For mixed requests, do not estimate work already
  included in the SOW.
- Do not assign 0 hours to genuinely new development.
- Estimate conservatively when evidence is uncertain.
- Do not invent previous charges or payments.
- Do not calculate estimated cost.
- Python calculates the cost.
OUTPUT RULES:

Return valid JSON only.

Use exactly these five keys:

{
  "verdict": "in_scope, out_of_scope, or grey_area",
  "sow_clause_ids": [],
  "estimated_hours": 0,
  "reasoning": "Brief explanation based on the evidence",
  "evidence": []
}

The evidence list must contain integer memory indexes only.

Do not include estimated_cost_inr.
Do not include error.
Do not include Markdown formatting.
Do not include text before or after the JSON object.
"""


# ============================================================
# 3. BUILD USER PROMPT
# ============================================================

def build_user_prompt(message, sow, memory_context=None):

    prompt = f"""
STATEMENT OF WORK (SOW):

{json.dumps(sow, indent=2)}

CLIENT REQUEST:

{message}

MEMORY CONTEXT:
"""

    if memory_context is None:

        prompt += """
Memory is disabled.
Do not refer to previous requests, revisions,
history, or client patterns.
"""

    elif len(memory_context) == 0:

        prompt += """
No previous memories are available.
Do not invent previous requests or history.
"""

    else:

        for i, memory in enumerate(memory_context):

            prompt += (
                f"\n[M{i}]\n"
                f"Date: {memory.get('date', 'Unknown')}\n"
                f"Type: {memory.get('type', 'Unknown')}\n"
                f"Text: {memory.get('text', '')}\n"
            )

    prompt += """

DECISION INSTRUCTIONS:

1. Compare the client request with the SOW clauses
   and exclusions.

2. Use supplied memory only when it is relevant.

3. For design revisions, distinguish between a request
   and a revision round that was actually completed.

4. Do not assume that included revision rounds
   have been exhausted without supporting evidence.

5. For mixed or unclear requests, consider grey_area.

6. Cite only relevant SOW clause IDs.

7. Return relevant memory indexes as integers
   in the evidence list.

8. Estimate additional work using only:
   [0, 1, 2, 4, 6, 8, 12, 16, 20, 40]

Return valid JSON with exactly these five keys:

verdict
sow_clause_ids
estimated_hours
reasoning
evidence

Do not include estimated_cost_inr or error.
Return JSON only.
"""

    return prompt


# ============================================================
# 4. CALL GROQ LLM
# ============================================================

def call_llm(
    system_prompt,
    user_prompt,
    model=PRIMARY_MODEL
):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing from the .env file."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(

        model=model,

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        response_format={
            "type": "json_object"
        },

        temperature=0.2
    )

    return response.choices[0].message.content


# ============================================================
# 5. PARSE LLM RESPONSE
# ============================================================

def parse_llm_response(response_text):

    if not isinstance(response_text, str):
        return None

    try:

        # Remove Qwen thinking tags if present.
        response_text = re.sub(
            r"<think>.*?</think>",
            "",
            response_text,
            flags=re.DOTALL
        ).strip()

        # Remove optional Markdown JSON fences.
        response_text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response_text,
            flags=re.IGNORECASE
        ).strip()

        return json.loads(response_text)

    except (json.JSONDecodeError, TypeError):

        return None


# ============================================================
# 6. VALIDATE LLM RESULT
# ============================================================

def validate_result(result, memory_context, sow):

    if not isinstance(result, dict):
        return None

    verdict = result.get("verdict")

    if verdict not in ALLOWED_VERDICTS:
        return None

    hours = result.get("estimated_hours")

    if type(hours) is not int or hours not in ALLOWED_HOURS:
        return None

    clause_ids = result.get("sow_clause_ids")

    if not isinstance(clause_ids, list):
        return None

    if not all(isinstance(item, str) for item in clause_ids):
        return None

    actual_clause_ids = {
        clause.get("id")
        for clause in sow.get("clauses", [])
        if isinstance(clause, dict)
    }

    if any(item not in actual_clause_ids for item in clause_ids):
        return None

    evidence = result.get("evidence")

    if not isinstance(evidence, list):
        return None

    memory_count = len(memory_context or [])

    evidence = [
        item for item in evidence
        if type(item) is int and 0 <= item < memory_count
    ]

    reasoning = result.get("reasoning")

    if not isinstance(reasoning, str) or not reasoning.strip():
        return None

    rate = sow.get("extra_work_rate_inr_per_hour", 0)

    if type(rate) not in (int, float) or rate < 0:
        return None

    if verdict == "in_scope":
        hours = 0

    cost = hours * rate

    return {
        "verdict": verdict,
        "sow_clause_ids": clause_ids,
        "estimated_hours": hours,
        "estimated_cost_inr": cost,
        "reasoning": reasoning,
        "evidence": evidence,
        "error": None
    }

# ============================================================
# 7. SAFE ERROR RESULT
# ============================================================

def error_result(error_message):

    return {
        "verdict": "grey_area",
        "sow_clause_ids": [],
        "estimated_hours": 0,
        "estimated_cost_inr": 0,
        "reasoning": (
            "The AI service could not reliably "
            "process the request."
        ),
        "evidence": [],
        "error": str(error_message)
    }


# ============================================================
# 8. CLASSIFY USING A SPECIFIC MODEL
# ============================================================

def classify_with_model(
    message,
    sow,
    memory_context,
    model
):

    user_prompt = build_user_prompt(
        message,
        sow,
        memory_context
    )

    last_error = None

    for attempt in range(2):

        try:

            response = call_llm(
                SYSTEM_PROMPT,
                user_prompt,
                model
            )

            result = parse_llm_response(response)

            validated = validate_result(
                result,
                memory_context,
                sow
            )

            if validated is not None:
                return validated

            last_error = "Invalid or incomplete LLM response."

            user_prompt += """

IMPORTANT CORRECTION:

Your previous response did not pass validation.

Review the SOW, request, and supplied memory again.
Return a complete JSON object with exactly the
five required keys and valid values.

Return JSON only.
"""

        except Exception as error:

            last_error = (
                f"{type(error).__name__}: {error}"
            )

        if attempt == 0:
            time.sleep(2)

    return error_result(
        last_error or "Model failed after retry."
    )

# ============================================================
# 9. MAIN CLASSIFICATION FUNCTION
# ============================================================

def classify_request(
    message,
    sow,
    memory_context=None,
    model=PRIMARY_MODEL,
    use_fallback=True
):

    result = classify_with_model(
        message,
        sow,
        memory_context,
        model
    )

    # Use the fallback model if the selected model fails.
    if (
        use_fallback
        and result["error"] is not None
        and model != FALLBACK_MODEL
    ):

        result = classify_with_model(
            message,
            sow,
            memory_context,
            FALLBACK_MODEL
        )

    return result


# ============================================================
# 10. BUILD MEMORY CONTEXT FOR TESTING
# ============================================================

def build_memory_context(
    test_case,
    message_lookup
):

    memory_context = []

    for message_id in test_case.get(
        "related_message_ids",
        []
    ):

        if message_id in message_lookup:

            message = message_lookup[message_id]

            memory_context.append({

                "text": message["text"],

                "date": message["date"],

                "type": "related_message"

            })

    return memory_context


# ============================================================
# 11. EVALUATION OF BOTH MODELS
# ============================================================

def run_evaluation():

    with open(
        "data/sow.json",
        encoding="utf-8"
    ) as f:

        sow = json.load(f)

    with open(
        "data/messages.json",
        encoding="utf-8"
    ) as f:

        messages = json.load(f)

    with open(
        "data/test_cases.json",
        encoding="utf-8"
    ) as f:

        test_cases = json.load(f)

    selected_ids = [

        "msg-004",
        "msg-009",
        "msg-015",
        "msg-017",
        "msg-019",
        "msg-020"

    ]

    message_lookup = {

        message["id"]: message

        for message in messages

    }

    test_lookup = {

        case["message_id"]: case

        for case in test_cases

    }

    models = [

        PRIMARY_MODEL,
        FALLBACK_MODEL

    ]

    summaries = {}

    for model in models:

        print("\n")
        print("=" * 65)
        print("TESTING MODEL:", model)
        print("=" * 65)

        verdict_correct = 0
        verdict_total = 0

        summaries[model] = {

            "correct": 0,
            "total": 0

        }

        for message_id in selected_ids:

            if (
                message_id not in message_lookup
                or message_id not in test_lookup
            ):

                print(
                    "Missing test data:",
                    message_id
                )

                continue

            message = message_lookup[message_id]

            test_case = test_lookup[message_id]

            expected = test_case["verdict"]

            memory_context = build_memory_context(
                test_case,
                message_lookup
            )

            print("\n" + "-" * 55)

            print("MESSAGE:", message_id)

            print("CLIENT:", message["text"])

            print("EXPECTED:", expected)

            # ----------------------------------------
            # WITHOUT MEMORY
            # ----------------------------------------

            print("\n--- WITHOUT MEMORY ---")

            result_without = classify_request(

                message["text"],
                sow,
                None,
                model=model,
                use_fallback=False

            )

            print(
                json.dumps(
                    result_without,
                    indent=2,
                    ensure_ascii=False
                )
            )

            # ----------------------------------------
            # WITH RELATED MEMORY
            # ----------------------------------------

            print("\n--- WITH RELATED MEMORY ---")

            result_with = classify_request(

                message["text"],
                sow,
                memory_context,
                model=model,
                use_fallback=False

            )

            print(
                json.dumps(
                    result_with,
                    indent=2,
                    ensure_ascii=False
                )
            )

            # ----------------------------------------
            # VERDICT ACCURACY
            # ----------------------------------------

            if result_with["error"] is None:

                verdict_total += 1

                if result_with["verdict"] == expected:

                    verdict_correct += 1

            summaries[model]["correct"] = verdict_correct

            summaries[model]["total"] = verdict_total

        print("\nMODEL SUMMARY")

        print(
            "Correct verdicts:",
            verdict_correct,
            "/",
            verdict_total
        )

        if verdict_total:

            accuracy = (
                verdict_correct / verdict_total
            ) * 100

            print(
                "Verdict accuracy:",
                round(accuracy, 2),
                "%"
            )

    # --------------------------------------------
    # FINAL MODEL COMPARISON
    # --------------------------------------------

    print("\n")
    print("=" * 65)
    print("FINAL MODEL COMPARISON")
    print("=" * 65)

    for model, summary in summaries.items():

        print("\nMODEL:", model)

        print(
            "Correct:",
            summary["correct"],
            "/",
            summary["total"]
        )

        if summary["total"]:

            accuracy = (
                summary["correct"]
                / summary["total"]
            ) * 100

            print(
                "Accuracy:",
                round(accuracy, 2),
                "%"
            )


# ============================================================
# 12. RUN TESTS
# ============================================================

if __name__ == "__main__":

    run_evaluation()