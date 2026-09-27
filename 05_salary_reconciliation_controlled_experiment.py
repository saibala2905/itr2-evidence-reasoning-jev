import os
import json

from typesafe_sdk import TypeSafeClient, Score


# =========================================================
# TypeSafe / JEV client
# =========================================================

client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# Common source documents
# =========================================================

form16 = {
    "employer": "ABC Technologies Pvt Ltd",
    "basic_salary": 12_00_000,
    "hra": 4_80_000,
    "special_allowance": 2_40_000,
    "gross_salary": 19_20_000,
}

ais = {
    "employer": "ABC Technologies Private Limited",
    "salary": 19_20_000,
}


# =========================================================
# Test cases
# =========================================================

cases = {

    # -----------------------------------------------------
    # CASE A
    # Completely consistent
    # -----------------------------------------------------
    "CASE_A_CONSISTENT": {
        "description": "Form 16, AIS and ITR are consistent.",

        "itr": {
            "employer": "ABC Technologies",
            "basic_salary": 12_00_000,
            "hra": 4_80_000,
            "special_allowance": 2_40_000,
            "gross_salary": 19_20_000,
        },
    },


    # -----------------------------------------------------
    # CASE B
    # HRA mismatch only
    #
    # HRA differs, but gross salary is adjusted so that
    # the ITR remains internally consistent.
    # -----------------------------------------------------
    "CASE_B_HRA_MISMATCH": {
        "description": "HRA differs from Form 16, while ITR arithmetic is internally consistent.",

        "itr": {
            "employer": "ABC Technologies",
            "basic_salary": 12_00_000,

            # Form 16 = 4.80L
            # ITR      = 5.50L
            "hra": 5_50_000,

            "special_allowance": 2_40_000,

            # 12.00 + 5.50 + 2.40 = 19.90L
            "gross_salary": 19_90_000,
        },
    },


    # -----------------------------------------------------
    # CASE C
    # Gross salary arithmetic mismatch only
    #
    # All components agree with Form 16, but declared
    # gross salary is incorrect.
    # -----------------------------------------------------
    "CASE_C_GROSS_MISMATCH": {
        "description": "Salary components agree, but declared gross salary is incorrect.",

        "itr": {
            "employer": "ABC Technologies",
            "basic_salary": 12_00_000,
            "hra": 4_80_000,
            "special_allowance": 2_40_000,

            # Correct = 19.20L
            # Deliberately declared = 20.20L
            "gross_salary": 20_20_000,
        },
    },


    # -----------------------------------------------------
    # CASE D
    # Both HRA and gross salary mismatch
    # -----------------------------------------------------
    "CASE_D_BOTH_MISMATCH": {
        "description": "Both HRA and gross salary differ from the source records.",

        "itr": {
            "employer": "ABC Technologies",
            "basic_salary": 12_00_000,

            # Form 16 = 4.80L
            "hra": 5_50_000,

            "special_allowance": 2_40_000,

            # Components total 19.90L
            # Declared gross = 20.90L
            "gross_salary": 20_90_000,
        },
    },
}


# =========================================================
# Score criteria
# =========================================================

criteria = [
    "The records are fully consistent and there is no material discrepancy.",

    "The primary discrepancy is a salary-component mismatch, such as HRA.",

    "The primary discrepancy is a gross-salary mismatch between the ITR and source documents.",

    "The discrepancy is primarily an internal arithmetic or data-entry inconsistency in the ITR.",

    "The discrepancy is primarily caused by employer-name variation.",

    "The discrepancy may be explained by a reporting difference between AIS and Form 16.",
]


# =========================================================
# Run each case
# =========================================================

all_results = {}


for case_name, case_data in cases.items():

    print("\n")
    print("=" * 70)
    print(case_name)
    print("=" * 70)

    print("\nDescription:")
    print(case_data["description"])

    itr = case_data["itr"]


    # -----------------------------------------------------
    # Deterministic arithmetic calculation
    # -----------------------------------------------------

    expected_gross = (
        itr["basic_salary"]
        + itr["hra"]
        + itr["special_allowance"]
    )

    declared_gross = itr["gross_salary"]

    arithmetic_difference = declared_gross - expected_gross

    arithmetic_valid = (
        expected_gross == declared_gross
    )


    # -----------------------------------------------------
    # Score question
    # -----------------------------------------------------

    score_question = Score(
        instructions={
            "form16": form16,
            "ais": ais,
            "itr": itr,

            "task": (
                "Analyze the relationship between Form 16, AIS and ITR "
                "salary records. Determine which of the supplied "
                "explanations best describes the observed consistency "
                "or discrepancy."
            ),
        },

        criteria=criteria,
    )


    # -----------------------------------------------------
    # Execute JEV
    # -----------------------------------------------------

    result = client.system_one(
        state={
            "form16": form16,
            "ais": ais,
            "itr": itr,
        },

        questions={
            "salary_reconciliation_diagnosis": score_question,
        },
    )


    # -----------------------------------------------------
    # Extract answer
    # -----------------------------------------------------

    answer = result.answers["salary_reconciliation_diagnosis"]


    # -----------------------------------------------------
    # Convert answer to JSON-compatible structure
    # -----------------------------------------------------

    if hasattr(answer, "model_dump"):
        score_result = answer.model_dump()

    elif hasattr(answer, "__dict__"):
        score_result = answer.__dict__

    else:
        score_result = str(answer)


    # -----------------------------------------------------
    # Store complete experiment result
    # -----------------------------------------------------

    all_results[case_name] = {
        "description": case_data["description"],

        "inputs": {
            "form16": form16,
            "ais": ais,
            "itr": itr,
        },

        "deterministic_validation": {
            "expected_gross_salary": expected_gross,
            "declared_gross_salary": declared_gross,
            "difference": arithmetic_difference,
            "valid": arithmetic_valid,
        },

        "jev_score": score_result,
    }


    # -----------------------------------------------------
    # Print result
    # -----------------------------------------------------

    print("\nJEV SCORE RESULT:")
    print(answer)

    print("\nDETERMINISTIC VALIDATION:")

    print(
        f"Expected gross salary : ₹{expected_gross:,}"
    )

    print(
        f"Declared gross salary : ₹{declared_gross:,}"
    )

    print(
        f"Difference             : ₹{arithmetic_difference:,}"
    )

    print(
        f"Arithmetic valid       : {arithmetic_valid}"
    )


# =========================================================
# Print complete JSON
# =========================================================

print("\n")
print("=" * 70)
print("COMPLETE EXPERIMENT JSON")
print("=" * 70)

print(
    json.dumps(
        all_results,
        indent=2,
        ensure_ascii=False,
    )
)