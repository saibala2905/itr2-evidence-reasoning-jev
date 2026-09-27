import json

from typesafe_sdk import (
    TypeSafeClient,
    Choice,
    Score,
)


# ============================================================
# EXPERIMENT 17
# ADVERSARIAL / AMBIGUOUS EVIDENCE
# ============================================================
#
# Purpose:
#
# Test how JEV behaves when the evidence is:
#
#   1. Clearly consistent
#   2. Different only in naming
#   3. Similar but potentially different entities
#   4. Potentially duplicated
#   5. Transaction identifiers conflict
#   6. Fundamentally insufficient to determine the answer
#
#
# The goal is NOT simply to get the "right" answer.
#
# We want to observe:
#
#   - Choice
#   - Score probability distribution
#   - Confidence
#
# in clear vs ambiguous situations.
#
# ============================================================


# ============================================================
# TEST CASES
# ============================================================

cases = [

    # --------------------------------------------------------
    # CASE 01
    # CLEARLY CONSISTENT
    # --------------------------------------------------------

    {
        "id": "CASE_01_CLEAR",

        "description": """
        FORM 16

        Employer:
        ABC Technologies Private Limited

        Gross salary:
        1,920,000


        AIS

        Employer:
        ABC Technologies Pvt Ltd

        Salary income:
        1,920,000


        ITR

        Employer:
        ABC Technologies

        Gross salary:
        1,920,000


        The employer names differ only in how the organization
        name is represented.

        All three sources report the same salary amount.
        """,

        "expected_category": "CONSISTENT",
    },


    # --------------------------------------------------------
    # CASE 02
    # NAMING VARIATION
    # --------------------------------------------------------

    {
        "id": "CASE_02_NAMING_VARIATION",

        "description": """
        FORM 16

        Employer:
        Infosys Limited


        AIS

        Employer:
        Infosys Ltd.


        ITR

        Employer:
        Infosys


        Salary reported by all sources:
        2,400,000


        No other employer information is available.
        """,

        "expected_category": "NAMING_VARIATION",
    },


    # --------------------------------------------------------
    # CASE 03
    # SIMILAR BUT DIFFERENT EMPLOYERS
    # --------------------------------------------------------

    {
        "id": "CASE_03_SIMILAR_EMPLOYERS",

        "description": """
        FORM 16

        Employer:
        ABC Technologies Pvt Ltd

        Gross salary:
        1,920,000


        AIS

        Employer:
        ABC Technology Services Pvt Ltd

        Salary:
        1,920,000


        ITR

        Employer:
        ABC Technologies Services

        Gross salary:
        1,920,000


        The names are similar but are not identical.

        No employer TAN, address, payroll identifier,
        or other legal-entity identifier is available.
        """,

        "expected_category": "AMBIGUOUS",
    },


    # --------------------------------------------------------
    # CASE 04
    # POSSIBLE DUPLICATE
    # --------------------------------------------------------

    {
        "id": "CASE_04_POSSIBLE_DUPLICATE",

        "description": """
        BANK RECORD 1

        Bank:
        ABC Bank

        Account:
        XXXX1234

        FD Interest:
        35,000


        BANK RECORD 2

        Bank:
        ABC Bank

        Account:
        XXXX1234

        FD Interest:
        35,000


        AIS

        Interest income:
        35,000


        ITR

        Interest income:
        35,000


        Both bank records have the same bank, account,
        and amount.

        It is unclear whether the second record is a
        duplicate representation or a separate source
        record.
        """,

        "expected_category": "DUPLICATE_OR_OVERLAP",
    },


    # --------------------------------------------------------
    # CASE 05
    # TRANSACTION MISMATCH
    # --------------------------------------------------------

    {
        "id": "CASE_05_TRANSACTION_MISMATCH",

        "description": """
        DONATION RECEIPT

        Institution:
        ABC Charitable Trust

        Amount:
        50,000

        Transaction reference:
        TXN123456


        BANK

        Institution:
        ABC Charitable Trust

        Amount:
        50,000

        Transaction reference:
        TXN123456


        ITR

        Institution:
        ABC Charitable Trust

        Amount:
        50,000

        Transaction reference:
        TXN999999


        The amount and institution are identical, but the
        transaction reference in the ITR differs from the
        receipt and bank evidence.
        """,

        "expected_category": "TRANSACTION_MISMATCH",
    },


    # --------------------------------------------------------
    # CASE 06
    # INSUFFICIENT EVIDENCE
    # --------------------------------------------------------

    {
        "id": "CASE_06_INSUFFICIENT",

        "description": """
        ITR

        Interest income:
        95,000


        Taxpayer states that the amount is correct.


        No AIS data is available.

        No bank statement is available.

        No Form 26AS information is available.

        No interest certificate is available.


        There is therefore no independent source against
        which the ITR amount can be reconciled.
        """,

        "expected_category": "INSUFFICIENT_EVIDENCE",
    },


    # --------------------------------------------------------
    # CASE 07
    # CONFLICTING SOURCES
    # --------------------------------------------------------

    {
        "id": "CASE_07_CONFLICTING_SOURCES",

        "description": """
        FORM 16

        Employer:
        ABC Technologies Pvt Ltd

        Gross salary:
        1,920,000


        AIS

        Employer:
        ABC Technologies Pvt Ltd

        Salary:
        2,100,000


        ITR

        Employer:
        ABC Technologies Pvt Ltd

        Gross salary:
        2,000,000


        No payroll statement, revised Form 16,
        employer confirmation, or other evidence
        is available.


        All three sources refer to the same apparent employer,
        but the reported salary amounts conflict.
        """,

        "expected_category": "AMBIGUOUS",
    },
]


# ============================================================
# JEV CLASSIFICATION
# ============================================================

classification_question = Choice(

    instructions=(
        "Analyze the supplied evidence carefully. "
        "Distinguish between clear consistency, simple naming "
        "variation, duplicate or overlapping evidence, "
        "transaction mismatch, ambiguity, and insufficient "
        "evidence. Do not assume that similar names represent "
        "the same legal entity unless the supplied evidence "
        "supports that conclusion."
    ),

    criteria={

        "CONSISTENT":
            (
                "The supplied records are materially consistent "
                "and no material discrepancy is established."
            ),

        "NAMING_VARIATION":
            (
                "The primary difference is a variation in how "
                "the same apparent organization or entity is named."
            ),

        "DUPLICATE_OR_OVERLAP":
            (
                "The evidence contains records that may represent "
                "the same underlying transaction or source and "
                "could be duplicated or overlapping."
            ),

        "TRANSACTION_MISMATCH":
            (
                "The transaction identifier or equivalent "
                "transaction-level evidence differs."
            ),

        "AMBIGUOUS":
            (
                "Multiple plausible interpretations remain and "
                "the supplied evidence is insufficient to choose "
                "between them reliably."
            ),

        "INSUFFICIENT_EVIDENCE":
            (
                "There is not enough independent evidence to "
                "determine whether the claim is supported."
            ),
    },
)


# ============================================================
# JEV DIAGNOSIS
# ============================================================

diagnosis_question = Score(

    instructions=(
        "Analyze the supplied evidence and assess the competing "
        "explanations. Pay particular attention to ambiguity, "
        "missing identifiers, duplicate records, and conflicting "
        "source amounts. Do not invent information that is not "
        "present in the case."
    ),

    criteria=[

        (
            "The evidence represents the same underlying "
            "information and is fully consistent."
        ),

        (
            "The differences are primarily naming or formatting "
            "variations."
        ),

        (
            "The records may represent duplicate or overlapping "
            "evidence."
        ),

        (
            "A transaction identifier or transaction-level "
            "attribute does not match."
        ),

        (
            "The sources contain genuinely conflicting values."
        ),

        (
            "There is insufficient evidence to determine "
            "which interpretation is correct."
        ),
    ],
)


# ============================================================
# SERIALIZATION
# ============================================================

def dump_answer(answer):

    if hasattr(answer, "model_dump"):
        return answer.model_dump()

    return str(answer)


# ============================================================
# RUN ONE CASE
# ============================================================

def run_case(client, case):

    response = client.system_one(

        state={
            "case_id":
                case["id"],

            "evidence":
                case["description"],
        },

        questions={

            "classification":
                classification_question,

            "diagnosis":
                diagnosis_question,
        },
    )

    classification = (
        response.answers["classification"]
    )

    diagnosis = (
        response.answers["diagnosis"]
    )

    classification_result = dump_answer(
        classification
    )

    diagnosis_result = dump_answer(
        diagnosis
    )

    return {

        "case_id":
            case["id"],

        "expected_category":
            case["expected_category"],

        "jev": {

            "classification":
                classification_result,

            "diagnosis":
                diagnosis_result,
        },
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\nRunning adversarial / ambiguous evidence experiment..."
    )

    results = []

    with TypeSafeClient() as client:

        for case in cases:

            print(
                f"Processing {case['id']}..."
            )

            result = run_case(
                client,
                case,
            )

            results.append(result)


    # ========================================================
    # BASIC ANALYSIS
    # ========================================================

    classification_matches = 0

    confidence_values = []

    for result in results:

        classification = (
            result["jev"]["classification"]
        )

        predicted = (
            classification.get("choice")
            if isinstance(
                classification,
                dict
            )
            else None
        )

        confidence = (
            classification.get("confidence")
            if isinstance(
                classification,
                dict
            )
            else None
        )

        if predicted == result["expected_category"]:
            classification_matches += 1

        if isinstance(confidence, (int, float)):
            confidence_values.append(
                confidence
            )


    total = len(results)

    evaluation = {

        "total_cases":
            total,

        "expected_category_matches":
            classification_matches,

        "exact_category_match_rate":
            (
                classification_matches / total
                if total > 0
                else 0
            ),

        "average_jev_confidence":
            (
                sum(confidence_values)
                / len(confidence_values)
                if confidence_values
                else None
            ),
    }


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    output = {

        "experiment":
            "Adversarial and Ambiguous Evidence",

        "purpose": (
            "Evaluate JEV behavior when evidence is clear, "
            "similar, duplicated, conflicting, or incomplete."
        ),

        "evaluation":
            evaluation,

        "cases":
            results,
    }


    print(
        "\n========== JSON ==========\n"
    )

    print(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        )
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()