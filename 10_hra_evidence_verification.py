import os
import json

from typesafe_sdk import TypeSafeClient, Noul, NoulCriteria


client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# Evidence
# =========================================================

form16 = {
    "hra_received": 4_80_000,
}


rent_receipts = {
    "monthly_rent": 20_000,
    "months": 12,
    "annual_rent": 2_40_000,
}


bank_records = {
    "rent_payments": 2_40_000,
}


itr = {
    "hra_claimed": 4_80_000,
}


# =========================================================
# Noul questions
# =========================================================

questions = {

    "hra_supported_by_form16": Noul(
        instructions={
            "form16": form16,
            "itr": itr,
        },
        criteria=NoulCriteria(
            true="The HRA claim is not supported by Form 16.",
            false="The HRA claim is supported by Form 16.",
        ),
    ),

    "hra_supported_by_rent_evidence": Noul(
        instructions={
            "rent_receipts": rent_receipts,
            "bank_records": bank_records,
            "itr": itr,
        },
        criteria=NoulCriteria(
            true=(
                "The available rent receipts and bank records "
                "do not support the HRA claim."
            ),
            false=(
                "The available rent receipts and bank records "
                "support the HRA claim."
            ),
        ),
    ),

    "hra_evidence_consistent": Noul(
        instructions={
            "form16": form16,
            "rent_receipts": rent_receipts,
            "bank_records": bank_records,
            "itr": itr,
        },
        criteria=NoulCriteria(
            true=(
                "The HRA claim is inconsistent with the "
                "available supporting evidence."
            ),
            false=(
                "The HRA claim is consistent with the "
                "available supporting evidence."
            ),
        ),
    ),
}


# =========================================================
# Run
# =========================================================

result = client.system_one(
    state={
        "form16": form16,
        "rent_receipts": rent_receipts,
        "bank_records": bank_records,
        "itr": itr,
    },
    questions=questions,
)


# =========================================================
# Deterministic evidence calculation
# =========================================================

annual_rent = (
    rent_receipts["monthly_rent"]
    * rent_receipts["months"]
)

deterministic = {
    "hra_claimed": itr["hra_claimed"],
    "hra_received": form16["hra_received"],
    "annual_rent": annual_rent,
    "bank_rent_payments": bank_records["rent_payments"],
    "rent_evidence_matches_bank": (
        annual_rent == bank_records["rent_payments"]
    ),
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
    "form16": form16,
    "rent_receipts": rent_receipts,
    "bank_records": bank_records,
    "itr": itr,
    "deterministic_validation": deterministic,
    "jev": jev,
}


print("\n========== JSON ==========\n")
print(json.dumps(output, indent=2, ensure_ascii=False))