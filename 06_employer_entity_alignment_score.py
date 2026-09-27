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
# Test cases
# =========================================================

cases = {

    # -----------------------------------------------------
    # CASE A
    # Same employer, different legal-name formatting
    # -----------------------------------------------------
    "CASE_A_SAME_EMPLOYER": {
        "description": (
            "The three records use different representations "
            "of the same employer."
        ),

        "form16_employer": "ABC Technologies Pvt Ltd",
        "ais_employer": "ABC Technologies Private Limited",
        "itr_employer": "ABC Technologies",
    },


    # -----------------------------------------------------
    # CASE B
    # Same employer, minor textual variation
    # -----------------------------------------------------
    "CASE_B_SAME_EMPLOYER_VARIATION": {
        "description": (
            "The employer names differ in abbreviation and punctuation "
            "but refer to the same organization."
        ),

        "form16_employer": "Infosys Limited",
        "ais_employer": "Infosys Ltd.",
        "itr_employer": "Infosys",
    },


    # -----------------------------------------------------
    # CASE C
    # Clearly different employers
    # -----------------------------------------------------
    "CASE_C_DIFFERENT_EMPLOYERS": {
        "description": (
            "The records contain clearly different employer names."
        ),

        "form16_employer": "ABC Technologies Pvt Ltd",
        "ais_employer": "XYZ Consulting Services Pvt Ltd",
        "itr_employer": "XYZ Consulting Services",
    },


    # -----------------------------------------------------
    # CASE D
    # Similar-looking but different organizations
    # -----------------------------------------------------
    "CASE_D_SIMILAR_NAMES": {
        "description": (
            "The names are lexically similar but may represent "
            "different organizations."
        ),

        "form16_employer": "ABC Technologies Pvt Ltd",
        "ais_employer": "ABC Technology Services Pvt Ltd",
        "itr_employer": "ABC Technologies Services",
    },
}


# =========================================================
# Score criteria
#
# Each criterion represents a possible interpretation of
# the relationship between the employer names.
# =========================================================

criteria = [
    "All three employer names refer to the same underlying legal or organizational entity.",

    "The employer names refer to the same organization but use abbreviated, "
    "shortened, or different legal-name formats.",

    "The employer names are different and refer to different organizations.",

    "The names are similar but there is insufficient evidence to conclude "
    "that they refer to the same organization.",

    "The employer identity cannot be reliably determined from the supplied names alone.",
]


# =========================================================
# Run experiment
# =========================================================

all_results = {}


for case_name, case_data in cases.items():

    print("\n")
    print("=" * 75)
    print(case_name)
    print("=" * 75)

    print("\nDescription:")
    print(case_data["description"])

    print("\nEmployer names:")

    print(
        "Form 16 :",
        case_data["form16_employer"]
    )

    print(
        "AIS     :",
        case_data["ais_employer"]
    )

    print(
        "ITR     :",
        case_data["itr_employer"]
    )


    # -----------------------------------------------------
    # Score question
    # -----------------------------------------------------

    alignment_question = Score(
        instructions={
            "form16_employer": case_data["form16_employer"],
            "ais_employer": case_data["ais_employer"],
            "itr_employer": case_data["itr_employer"],

            "task": (
                "Determine whether the employer names appearing in "
                "Form 16, AIS and ITR refer to the same underlying "
                "employer entity. Consider legal-name variations, "
                "abbreviations, shortened names and meaningful "
                "differences between organizations."
            ),
        },

        criteria=criteria,
    )


    # -----------------------------------------------------
    # Execute JEV
    # -----------------------------------------------------

    result = client.system_one(
        state={
            "form16_employer": case_data["form16_employer"],
            "ais_employer": case_data["ais_employer"],
            "itr_employer": case_data["itr_employer"],
        },

        questions={
            "employer_entity_alignment": alignment_question,
        },
    )


    # -----------------------------------------------------
    # Get answer
    # -----------------------------------------------------

    answer = result.answers["employer_entity_alignment"]


    # -----------------------------------------------------
    # Convert to JSON
    # -----------------------------------------------------

    if hasattr(answer, "model_dump"):
        score_result = answer.model_dump()

    elif hasattr(answer, "__dict__"):
        score_result = answer.__dict__

    else:
        score_result = str(answer)


    # -----------------------------------------------------
    # Store result
    # -----------------------------------------------------

    all_results[case_name] = {
        "description": case_data["description"],

        "employer_names": {
            "form16": case_data["form16_employer"],
            "ais": case_data["ais_employer"],
            "itr": case_data["itr_employer"],
        },

        "jev_score": score_result,
    }


    # -----------------------------------------------------
    # Print result
    # -----------------------------------------------------

    print("\nJEV RESULT:")
    print(answer)


# =========================================================
# Complete JSON output
# =========================================================

print("\n")
print("=" * 75)
print("COMPLETE EXPERIMENT JSON")
print("=" * 75)

print(
    json.dumps(
        all_results,
        indent=2,
        ensure_ascii=False,
    )
)