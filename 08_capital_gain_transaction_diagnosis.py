import os
import json

from typesafe_sdk import TypeSafeClient, Score


client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# Broker transaction
# =========================================================

broker = {
    "security": "INFOSYS",
    "quantity": 100,
    "purchase_price": 1400,
    "sale_price": 1600,
    "purchase_date": "2025-04-10",
    "sale_date": "2025-09-20",
}


# =========================================================
# AIS
# =========================================================

ais = {
    "security": "INFOSYS",
    "quantity": 100,
    "sale_value": 160_000,
}


# =========================================================
# ITR
# =========================================================

itr = {
    "security": "INFOSYS",
    "quantity": 100,
    "sale_value": 160_000,

    # Correct simple gain would be:
    # (1600 - 1400) * 100 = 20,000
    #
    # Deliberate error:
    "capital_gain": 12_000,
}


# =========================================================
# Score
# =========================================================

question = Score(
    instructions={
        "broker": broker,
        "ais": ais,
        "itr": itr,

        "task": (
            "Determine the most likely explanation for the "
            "capital-gain discrepancy."
        ),
    },

    criteria=[
        "The capital gain declared in the ITR is fully consistent with the broker transaction.",

        "The acquisition cost or purchase price used in the ITR is incorrect.",

        "The sale value or sale proceeds used in the ITR is incorrect.",

        "The transaction quantity differs between the source records and ITR.",

        "The capital gain contains an ITR calculation or data-entry error.",

        "The transaction may be duplicated or incorrectly represented in one of the sources.",
    ],
)


result = client.system_one(
    state={
        "broker": broker,
        "ais": ais,
        "itr": itr,
    },
    questions={
        "capital_gain_diagnosis": question,
    },
)


# =========================================================
# Deterministic calculation
# =========================================================

expected_gain = (
    broker["sale_price"] - broker["purchase_price"]
) * broker["quantity"]

declared_gain = itr["capital_gain"]

deterministic = {
    "expected_gain": expected_gain,
    "declared_gain": declared_gain,
    "difference": declared_gain - expected_gain,
    "valid": declared_gain == expected_gain,
}


# =========================================================
# JSON
# =========================================================

answer = result.answers["capital_gain_diagnosis"]

jev = (
    answer.model_dump()
    if hasattr(answer, "model_dump")
    else str(answer)
)

output = {
    "broker": broker,
    "ais": ais,
    "itr": itr,
    "deterministic_validation": deterministic,
    "jev_score": jev,
}


print("\n========== JSON ==========\n")
print(json.dumps(output, indent=2, ensure_ascii=False))