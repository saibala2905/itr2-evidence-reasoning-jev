import json

from typesafe_sdk import (
    TypeSafeClient,
    Choice,
    Noul,
)


# ============================================================
# EXPERIMENT
# ============================================================
#
# Purpose:
#
# Test whether JEV can reason against an explicitly supplied
# CBDT validation rule rather than relying on an assumed
# tax rule.
#
# CBDT Rule used:
#
# ITR-2 AY 2026-27
# Category A
# Rule 22
#
# "In Schedule S, Sl. No. 1 Gross Salary
# (1a + 1b + 1c + 1d + 1e + 1f) should be consistent
# with sum of Sl. No. 1a+1b+1c+1d+1e +1f"
#
# Source:
# CBDT e-Filing Project
# ITR 2 – Validation Rules for AY 2026-27
# Version 1.0
# 26 May 2026
#
# ============================================================


# ============================================================
# CBDT RULE
# ============================================================

CBDT_RULE = {
    "rule_id": "ITR2_AY2026_27_RULE_22",

    "category": "Category A",

    "schedule": "Schedule S",

    "field": "Sl. No. 1 - Gross Salary",

    "rule": (
        "Gross Salary (1a + 1b + 1c + 1d + 1e + 1f) "
        "should be consistent with the sum of "
        "Sl. No. 1a + 1b + 1c + 1d + 1e + 1f."
    ),

    "authoritative_source": (
        "CBDT e-Filing Project, "
        "ITR 2 – Validation Rules for AY 2026-27, "
        "Version 1.0, 26 May 2026, Rule 22"
    ),
}


# ============================================================
# TEST CASES
# ============================================================

cases = [

    # --------------------------------------------------------
    # CASE 01
    # --------------------------------------------------------

    {
        "id": "CASE_01_VALID",

        "itr": {
            "schedule": "S",

            "salary_components": {
                "1a": 1200000,
                "1b": 480000,
                "1c": 240000,
                "1d": 0,
                "1e": 0,
                "1f": 0,
            },

            "gross_salary": 1920000,
        },

        "description": (
            "Gross salary equals the sum of all six salary "
            "components."
        ),

        "expected": "RULE_SATISFIED",
    },


    # --------------------------------------------------------
    # CASE 02
    # --------------------------------------------------------

    {
        "id": "CASE_02_ARITHMETIC_VIOLATION",

        "itr": {
            "schedule": "S",

            "salary_components": {
                "1a": 1200000,
                "1b": 480000,
                "1c": 240000,
                "1d": 0,
                "1e": 0,
                "1f": 0,
            },

            "gross_salary": 2090000,
        },

        "description": (
            "Gross salary is 2,090,000 while the sum of the "
            "six salary components is 1,920,000."
        ),

        "expected": "RULE_VIOLATED",
    },


    # --------------------------------------------------------
    # CASE 03
    # --------------------------------------------------------

    {
        "id": "CASE_03_SOURCE_DISCREPANCY_ONLY",

        "source_evidence": {
            "form16_gross_salary": 1920000,
        },

        "itr": {
            "schedule": "S",

            "salary_components": {
                "1a": 1300000,
                "1b": 500000,
                "1c": 200000,
                "1d": 0,
                "1e": 0,
                "1f": 0,
            },

            "gross_salary": 2000000,
        },

        "description": (
            "The ITR is internally consistent because the "
            "gross salary equals its six components, but "
            "external Form 16 evidence reports a different "
            "gross salary."
        ),

        "expected": "RULE_SATISFIED_BUT_SOURCE_DISCREPANCY",
    },
]


# ============================================================
# DETERMINISTIC VALIDATION
# ============================================================

def deterministic_validation(case):

    itr = case["itr"]

    components = itr["salary_components"]

    calculated_gross = sum(
        components.get(field, 0)
        for field in [
            "1a",
            "1b",
            "1c",
            "1d",
            "1e",
            "1f",
        ]
    )

    declared_gross = itr["gross_salary"]

    rule_satisfied = (
        calculated_gross == declared_gross
    )

    result = {
        "calculated_gross_salary":
            calculated_gross,

        "declared_gross_salary":
            declared_gross,

        "difference":
            declared_gross - calculated_gross,

        "rule_satisfied":
            rule_satisfied,
    }

    # --------------------------------------------------------
    # External evidence comparison
    # --------------------------------------------------------

    source_evidence = case.get(
        "source_evidence"
    )

    if source_evidence:

        source_gross = source_evidence[
            "form16_gross_salary"
        ]

        result["source_gross_salary"] = source_gross

        result["source_vs_itr_difference"] = (
            declared_gross - source_gross
        )

        result["source_matches_itr"] = (
            declared_gross == source_gross
        )

    return result


# ============================================================
# BUILD JEV INPUT
# ============================================================

def build_case(case, deterministic):

    return {
        "validation_rule": CBDT_RULE,

        "case_id": case["id"],

        "case_description":
            case["description"],

        "itr_data":
            case["itr"],

        "source_evidence":
            case.get("source_evidence"),

        "deterministic_validation":
            deterministic,
    }


# ============================================================
# RUN JEV
# ============================================================

def run_jev(client, case, deterministic):

    jev_case = build_case(
        case,
        deterministic,
    )

    # --------------------------------------------------------
    # Choice
    # --------------------------------------------------------

    classification = Choice(

        instructions=(
            "Evaluate the taxpayer data against the supplied "
            "CBDT validation rule. Distinguish between an "
            "actual violation of the supplied rule and a "
            "discrepancy that exists only between the ITR "
            "and external evidence."
        ),

        criteria={

            "RULE_SATISFIED":
                (
                    "The ITR satisfies the supplied CBDT "
                    "validation rule."
                ),

            "RULE_VIOLATED":
                (
                    "The ITR violates the supplied CBDT "
                    "validation rule."
                ),

            "RULE_SATISFIED_BUT_SOURCE_DISCREPANCY":
                (
                    "The ITR satisfies the supplied rule "
                    "internally, but external source evidence "
                    "differs from the ITR."
                ),

            "INSUFFICIENT_EVIDENCE":
                (
                    "There is insufficient information to "
                    "determine whether the supplied rule "
                    "is satisfied."
                ),
        },
    )


    # --------------------------------------------------------
    # Noul
    # --------------------------------------------------------

    rule_verification = Noul(

        instructions=(
            "Verify the supplied CBDT validation rule using "
            "only the supplied taxpayer data and evidence. "
            "Do not introduce additional tax rules. "
            "Determine whether the ITR data satisfies the "
            "specific rule provided."
        ),
    )


    # --------------------------------------------------------
    # System One
    # --------------------------------------------------------

    response = client.system_one(

        state={
            "case": jev_case,
        },

        questions={
            "classification":
                classification,

            "rule_verification":
                rule_verification,
        },
    )


    return response


# ============================================================
# SERIALIZATION
# ============================================================

def dump_answer(answer):

    if hasattr(answer, "model_dump"):
        return answer.model_dump()

    return str(answer)


# ============================================================
# MAIN
# ============================================================

def main():

    results = []

    print(
        "\nRunning CBDT rule-grounded validation experiment..."
    )

    with TypeSafeClient() as client:

        for case in cases:

            print(
                f"\nProcessing {case['id']}..."
            )

            deterministic = (
                deterministic_validation(case)
            )

            response = run_jev(
                client,
                case,
                deterministic,
            )

            classification = (
                response.answers["classification"]
            )

            rule_verification = (
                response.answers["rule_verification"]
            )

            result = {

                "case_id":
                    case["id"],

                "expected":
                    case["expected"],

                "deterministic_validation":
                    deterministic,

                "jev": {

                    "classification":
                        dump_answer(
                            classification
                        ),

                    "rule_verification":
                        dump_answer(
                            rule_verification
                        ),
                },
            }

            results.append(result)


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {

        "total_cases":
            len(results),

        "deterministic_rule_violations":
            sum(
                1
                for result in results
                if not result[
                    "deterministic_validation"
                ]["rule_satisfied"]
            ),

        "deterministic_rule_satisfied":
            sum(
                1
                for result in results
                if result[
                    "deterministic_validation"
                ]["rule_satisfied"]
            ),
    }


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    output = {

        "experiment":
            "CBDT Rule-Grounded ITR Validation",

        "rule":
            CBDT_RULE,

        "summary":
            summary,

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