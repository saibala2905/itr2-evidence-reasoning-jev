import os
import json

from typesafe_sdk import TypeSafeClient, Score


client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# Bank records
# =========================================================

bank_records = [
    {
        "bank": "ABC Bank",
        "type": "FD Interest",
        "amount": 35_000,
    },
    {
        "bank": "XYZ Bank",
        "type": "FD Interest",
        "amount": 42_000,
    },
    {
        "bank": "ABC Bank",
        "type": "Savings Interest",
        "amount": 18_000,
    },
]


# =========================================================
# AIS
# =========================================================

ais = {
    "interest_income": 95_000,
}


# =========================================================
# ITR
# =========================================================

itr = {
    "interest_income": 77_000,
}


# =========================================================
# Deterministic total
# =========================================================

bank_total = sum(
    record["amount"]
    for record in bank_records
)

deterministic = {
    "bank_total": bank_total,
    "ais_total": ais["interest_income"],
    "itr_total": itr["interest_income"],
    "bank_vs_ais_difference": (
        bank_total - ais["interest_income"]
    ),
    "bank_vs_itr_difference": (
        bank_total - itr["interest_income"]
    ),
}


# =========================================================
# Score
# =========================================================

question = Score(
    instructions={
        "bank_records": bank_records,
        "ais": ais,
        "itr": itr,

        "task": (
            "Determine the most likely explanation for the "
            "difference between bank interest records, AIS "
            "and ITR interest income."
        ),
    },

    criteria=[
        "The ITR interest income is fully supported by the bank records and AIS.",

        "The ITR is missing one or more interest-income sources.",

        "AIS contains interest income that is not reflected in the ITR.",

        "The bank records contain information that differs from AIS.",

        "The ITR interest amount appears to contain a transcription or data-entry error.",

        "There may be duplicate or overlapping interest records.",
    ],
)


result = client.system_one(
    state={
        "bank_records": bank_records,
        "ais": ais,
        "itr": itr,
    },
    questions={
        "interest_reconciliation": question,
    },
)


answer = result.answers["interest_reconciliation"]

jev = (
    answer.model_dump()
    if hasattr(answer, "model_dump")
    else str(answer)
)


# =========================================================
# Output
# =========================================================

output = {
    "bank_records": bank_records,
    "ais": ais,
    "itr": itr,
    "deterministic_validation": deterministic,
    "jev_score": jev,
}


print("\n========== JSON ==========\n")
print(json.dumps(output, indent=2, ensure_ascii=False))