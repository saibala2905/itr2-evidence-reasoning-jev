import os
import json

from typesafe_sdk import TypeSafeClient, Score


# ---------------------------------------------------------
# TypeSafe / JEV client
# ---------------------------------------------------------

client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# ---------------------------------------------------------
# Source records
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Deliberately inconsistent ITR data
# ---------------------------------------------------------

itr = {
    "employer": "ABC Technologies",

    "basic_salary": 12_00_000,

    # Deliberate discrepancy
    "hra": 5_50_000,

    "special_allowance": 2_40_000,

    # 12,00,000 + 5,50,000 + 2,40,000
    # = 19,90,000
    #
    # We intentionally declare 20,90,000 in the ITR.
    "gross_salary": 20_90_000,
}


# ---------------------------------------------------------
# Score question
#
# The criteria represent competing explanations for the
# discrepancy between Form 16, AIS and ITR.
# ---------------------------------------------------------

diagnosis_question = Score(
    instructions={
        "form16": form16,
        "ais": ais,
        "itr": itr,

        "task": (
            "Analyze the differences between Form 16, AIS and ITR "
            "salary records and determine which explanation best "
            "accounts for the observed discrepancy."
        ),
    },

    criteria=[
        "The difference is primarily caused by employer-name variation.",

        "The difference is primarily caused by a gross-salary mismatch "
        "between the ITR and the source documents.",

        "The difference is primarily caused by a salary-component mismatch "
        "such as HRA or another component.",

        "The difference may be explained by a reporting difference between "
        "AIS and Form 16.",

        "The difference is consistent with an ITR transcription or data-entry "
        "error.",

        "There is no material discrepancy between the records.",
    ],
)


# ---------------------------------------------------------
# Run System One
# ---------------------------------------------------------

result = client.system_one(
    state={
        "form16": form16,
        "ais": ais,
        "itr": itr,
    },
    questions={
        "salary_discrepancy_diagnosis": diagnosis_question,
    },
)


# ---------------------------------------------------------
# Print normal result
# ---------------------------------------------------------

print("\n========== RESULT ==========\n")

for name, answer in result.answers.items():
    print(name, "=>", answer)


# ---------------------------------------------------------
# Convert result to JSON
# ---------------------------------------------------------

json_output = {}

for name, answer in result.answers.items():

    if hasattr(answer, "model_dump"):
        json_output[name] = answer.model_dump()

    elif hasattr(answer, "__dict__"):
        json_output[name] = answer.__dict__

    else:
        json_output[name] = str(answer)


# ---------------------------------------------------------
# Print JSON
# ---------------------------------------------------------

print("\n========== JSON ==========\n")

print(
    json.dumps(
        json_output,
        indent=2,
        ensure_ascii=False,
    )
)


# ---------------------------------------------------------
# Deterministic arithmetic validation
# ---------------------------------------------------------

expected_gross_salary = (
    itr["basic_salary"]
    + itr["hra"]
    + itr["special_allowance"]
)

declared_gross_salary = itr["gross_salary"]

print("\n========== DETERMINISTIC VALIDATION ==========\n")

print(f"ITR basic salary       : ₹{itr['basic_salary']:,}")
print(f"ITR HRA                : ₹{itr['hra']:,}")
print(f"ITR special allowance : ₹{itr['special_allowance']:,}")

print(f"\nExpected gross salary  : ₹{expected_gross_salary:,}")
print(f"Declared gross salary  : ₹{declared_gross_salary:,}")

if expected_gross_salary != declared_gross_salary:
    difference = declared_gross_salary - expected_gross_salary

    print("\nSTATUS: ERROR")
    print(f"Gross salary mismatch  : ₹{difference:,}")
else:
    print("\nSTATUS: VALID")