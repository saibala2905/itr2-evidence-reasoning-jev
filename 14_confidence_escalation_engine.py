import json

from typesafe_sdk import (
    TypeSafeClient,
    Choice,
)


# ============================================================
# HELPER
# ============================================================

def dump_answer(answer):
    """
    Convert a TypeSafe answer object into JSON-serializable data.
    """
    if hasattr(answer, "model_dump"):
        return answer.model_dump()

    return str(answer)


# ============================================================
# EXPERIMENT CASES
# ============================================================

cases = [

    {
        "id": "CASE_01_CLEAR_AMOUNT_MISMATCH",

        "description": """
        Donation receipt:

        Institution:
        ABC Charitable Trust

        Donation amount:
        50,000

        Transaction reference:
        TXN123456


        Bank transaction:

        Institution:
        ABC Charitable Trust

        Amount:
        50,000

        Transaction reference:
        TXN123456


        ITR:

        Institution:
        ABC Charitable Trust

        Donation claimed:
        75,000

        Transaction reference:
        TXN123456


        The receipt and bank transaction agree with each other,
        but the ITR claims a higher donation amount.
        """,

        "expected_nature": "CLEAR_DISCREPANCY",
    },


    {
        "id": "CASE_02_CLEAR_CONSISTENCY",

        "description": """
        Form 16:

        Employer:
        ABC Technologies Private Limited

        Gross salary:
        1,920,000


        AIS:

        Employer:
        ABC Technologies Pvt Ltd

        Salary:
        1,920,000


        ITR:

        Employer:
        ABC Technologies

        Gross salary:
        1,920,000


        The employer names differ in their legal-name
        representation, but the salary amount is identical
        across all sources.
        """,

        "expected_nature": "CONSISTENT",
    },


    {
        "id": "CASE_03_AMBIGUOUS_EMPLOYER",

        "description": """
        Form 16:

        Employer:
        ABC Technologies Pvt Ltd

        Gross salary:
        1,920,000


        AIS:

        Employer:
        ABC Technology Services Pvt Ltd

        Salary:
        1,920,000


        ITR:

        Employer:
        ABC Technologies Services

        Gross salary:
        2,020,000


        No additional employer identity information,
        payroll records, or supporting documents are available.
        """,

        "expected_nature": "AMBIGUOUS",
    },


    {
        "id": "CASE_04_INSUFFICIENT_EVIDENCE",

        "description": """
        ITR:

        Interest income:
        95,000


        A taxpayer states that the interest income is correct.

        No AIS record, bank statement, Form 26AS record,
        interest certificate, or other supporting evidence
        has been supplied.
        """,

        "expected_nature": "INSUFFICIENT_EVIDENCE",
    },
]


# ============================================================
# EXPERIMENTAL ESCALATION POLICY
# ============================================================

def escalation_policy(confidence):
    """
    Experimental thresholds only.

    These thresholds are NOT tax rules and should not be
    interpreted as official CBDT thresholds.
    """

    if confidence is None:
        return {
            "level": "UNKNOWN",
            "action": "HUMAN_REVIEW",
        }

    if confidence >= 0.90:
        return {
            "level": "HIGH",
            "action": "AUTOMATED_REVIEW",
        }

    elif confidence >= 0.70:
        return {
            "level": "MEDIUM",
            "action": "ASSISTED_REVIEW",
        }

    else:
        return {
            "level": "LOW",
            "action": "HUMAN_REVIEW",
        }


# ============================================================
# RUN ONE CASE
# ============================================================

def run_case(client, case):

    question = Choice(
        instructions=(
            "Analyze the supplied taxpayer evidence and classify "
            "the evidentiary situation. Pay attention to whether "
            "the evidence clearly establishes a discrepancy, "
            "clearly supports consistency, or is insufficient "
            "or ambiguous."
        ),

        criteria={

            "CONSISTENT":
                "The supplied evidence is sufficiently consistent "
                "and does not demonstrate a material discrepancy.",

            "CLEAR_DISCREPANCY":
                "The supplied evidence clearly demonstrates "
                "a material discrepancy.",

            "AMBIGUOUS":
                "The evidence supports multiple plausible "
                "interpretations and does not clearly establish "
                "one explanation.",

            "INSUFFICIENT_EVIDENCE":
                "There is not enough evidence to determine "
                "whether the taxpayer information is supported.",
        },
    )

    response = client.system_one(
        state={
            "case_id": case["id"],
            "taxpayer_case": case["description"],
        },

        questions={
            "classification": question,
        },
    )

    answer = response.answers["classification"]

    result = dump_answer(answer)

    confidence = result.get("confidence")

    escalation = escalation_policy(confidence)

    return {
        "case_id": case["id"],

        "expected_nature":
            case["expected_nature"],

        "jev": result,

        "escalation": escalation,
    }


# ============================================================
# MAIN
# ============================================================

with TypeSafeClient() as client:

    results = []

    for case in cases:

        print(
            f"Running {case['id']}..."
        )

        result = run_case(
            client,
            case,
        )

        results.append(result)


# ============================================================
# EVALUATION
# ============================================================

evaluation = {

    "total_cases":
        len(results),

    "high_confidence_cases":
        sum(
            1
            for r in results
            if r["escalation"]["level"] == "HIGH"
        ),

    "medium_confidence_cases":
        sum(
            1
            for r in results
            if r["escalation"]["level"] == "MEDIUM"
        ),

    "low_confidence_cases":
        sum(
            1
            for r in results
            if r["escalation"]["level"] == "LOW"
        ),

    "human_review_cases":
        sum(
            1
            for r in results
            if r["escalation"]["action"] == "HUMAN_REVIEW"
        ),
}


# ============================================================
# FINAL OUTPUT
# ============================================================

output = {

    "experiment":
        "Confidence and Human Review Escalation",

    "note":
        "Confidence thresholds are experimental and are not "
        "official tax or CBDT thresholds.",

    "evaluation":
        evaluation,

    "cases":
        results,
}


print("\n========== JSON ==========\n")

print(
    json.dumps(
        output,
        indent=2,
        ensure_ascii=False,
    )
)