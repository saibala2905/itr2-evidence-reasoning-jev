import os
import json

from typesafe_sdk import TypeSafeClient, Choice, Noul, NoulCriteria


client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# ITR data
# =========================================================

itr = {
    "tax_regime": "NEW",

    "deductions": {
        "80C": 1_50_000,
        "80D": 25_000,
        "80G": 50_000,
        "80CCD_1B": 50_000,
    },
}


# =========================================================
# Choice
# =========================================================

regime_question = Choice(
    instructions={
        "itr": itr,

        "task": (
            "Identify the type of tax-regime and deduction "
            "conflict present in the ITR."
        ),
    },

    criteria={
        "NO_CONFLICT": (
            "The selected tax regime and claimed deductions "
            "are compatible."
        ),

        "80C_CONFLICT": (
            "The ITR claims a deduction under section 80C "
            "that conflicts with the selected regime."
        ),

        "80D_CONFLICT": (
            "The ITR claims a deduction under section 80D "
            "that conflicts with the selected regime."
        ),

        "80G_CONFLICT": (
            "The ITR claims a deduction under section 80G "
            "that conflicts with the selected regime."
        ),

        "MULTIPLE_DEDUCTION_CONFLICT": (
            "Multiple claimed deductions appear inconsistent "
            "with the selected tax regime."
        ),

        "OTHER": (
            "A different regime/deduction issue is present."
        ),
    },
)


# =========================================================
# Noul
# =========================================================

noul_question = Noul(
    instructions={
        "tax_regime": itr["tax_regime"],
        "deductions": itr["deductions"],

        "claim": (
            "The ITR claims Chapter VI-A deductions while "
            "the new tax regime is selected."
        ),
    },

    criteria=NoulCriteria(
        true=(
            "The deduction claims are inconsistent with "
            "the selected tax regime."
        ),
        false=(
            "The deduction claims are consistent with "
            "the selected tax regime."
        ),
    ),
)


# =========================================================
# Run
# =========================================================

result = client.system_one(
    state={
        "itr": itr,
    },
    questions={
        "regime_conflict": regime_question,
        "regime_verification": noul_question,
    },
)


# =========================================================
# Deterministic rule layer
# =========================================================

restricted_deductions = [
    "80C",
    "80D",
    "80G",
    "80CCD_1B",
]


conflicting = {
    name: amount
    for name, amount in itr["deductions"].items()
    if name in restricted_deductions and amount > 0
}


deterministic = {
    "tax_regime": itr["tax_regime"],
    "conflicting_deductions": conflicting,
    "conflict_detected": len(conflicting) > 0,
}


# =========================================================
# JSON
# =========================================================

jev = {}

for name, answer in result.answers.items():
    jev[name] = (
        answer.model_dump()
        if hasattr(answer, "model_dump")
        else str(answer)
    )


output = {
    "itr": itr,
    "deterministic_validation": deterministic,
    "jev": jev,
}


print("\n========== JSON ==========\n")
print(json.dumps(output, indent=2, ensure_ascii=False))