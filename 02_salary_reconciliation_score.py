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

itr = {
    "employer": "ABC Technologies",
    "basic_salary": 12_00_000,
    "hra": 4_80_000,
    "special_allowance": 2_40_000,
    "gross_salary": 19_20_000,
}


# ---------------------------------------------------------
# Score question
# ---------------------------------------------------------

score_question = Score(
    instructions={
        "form16": form16,
        "ais": ais,
        "itr": itr,
    },

    criteria=[
        "Employer identities are consistent across the records.",
        "Gross salary reported in the records is consistent.",
        "Basic salary reported in Form 16 and ITR is consistent.",
        "HRA reported in Form 16 and ITR is consistent.",
        "Special allowance reported in Form 16 and ITR is consistent.",
        "The ITR salary values can be reconciled with Form 16 and AIS.",
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
        "salary_reconciliation": score_question,
    },
)


# ---------------------------------------------------------
# Print normal result
# ---------------------------------------------------------

print("\n========== RESULT ==========\n")

for name, answer in result.answers.items():
    print(name, "=>", answer)


# ---------------------------------------------------------
# Convert Score result to JSON
# ---------------------------------------------------------

json_output = {}

for name, answer in result.answers.items():

    # Pydantic model
    if hasattr(answer, "model_dump"):
        json_output[name] = answer.model_dump()

    # Fallback for objects that may expose __dict__
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