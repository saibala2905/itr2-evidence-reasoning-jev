import os
import json

from typesafe_sdk import TypeSafeClient, Choice, Noul, NoulCriteria


client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# Donation receipt
# =========================================================

receipt = {
    "institution": "ABC Charitable Trust",
    "donation_amount": 50_000,
    "transaction_reference": "TXN123456",
    "ifsc": "ABCD0001234",
}


# =========================================================
# Bank transaction
# =========================================================

bank = {
    "transaction_reference": "TXN123456",
    "amount": 50_000,
    "beneficiary": "ABC Charitable Trust",
}


# =========================================================
# ITR
# =========================================================

itr = {
    "institution": "ABC Charitable Trust",
    "donation_amount": 75_000,
    "transaction_reference": "TXN123456",
    "ifsc": "ABCD0001234",
}


# =========================================================
# Choice
# =========================================================

classification = Choice(
    instructions={
        "receipt": receipt,
        "bank": bank,
        "itr": itr,

        "task": (
            "Classify the relationship between the donation "
            "claim and the available evidence."
        ),
    },

    criteria={
        "SUPPORTED": (
            "The donation amount, institution and transaction "
            "details are supported by the available evidence."
        ),

        "AMOUNT_MISMATCH": (
            "The institution and transaction can be matched, "
            "but the claimed donation amount differs from evidence."
        ),

        "TRANSACTION_MISMATCH": (
            "The transaction details in the ITR cannot be matched "
            "with the receipt or bank evidence."
        ),

        "MISSING_EVIDENCE": (
            "The ITR contains a donation claim but sufficient "
            "supporting evidence is unavailable."
        ),

        "OTHER": (
            "The evidence does not fit the other categories."
        ),
    },
)


# =========================================================
# Noul
# =========================================================

verification = Noul(
    instructions={
        "receipt": receipt,
        "bank": bank,
        "itr": itr,

        "claim": (
            "The ITR's ₹75,000 donation claim is supported "
            "by the donation receipt and bank transaction."
        ),
    },

    criteria=NoulCriteria(
        true=(
            "The ₹75,000 donation claim is not supported "
            "by the supplied evidence."
        ),
        false=(
            "The ₹75,000 donation claim is supported "
            "by the supplied evidence."
        ),
    ),
)


# =========================================================
# Run
# =========================================================

result = client.system_one(
    state={
        "receipt": receipt,
        "bank": bank,
        "itr": itr,
    },
    questions={
        "donation_classification": classification,
        "donation_verification": verification,
    },
)


# =========================================================
# Deterministic validation
# =========================================================

deterministic = {
    "receipt_amount": receipt["donation_amount"],
    "bank_amount": bank["amount"],
    "itr_amount": itr["donation_amount"],
    "receipt_bank_match": (
        receipt["donation_amount"]
        == bank["amount"]
    ),
    "itr_amount_difference": (
        itr["donation_amount"]
        - receipt["donation_amount"]
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
    "receipt": receipt,
    "bank": bank,
    "itr": itr,
    "deterministic_validation": deterministic,
    "jev": jev,
}


print("\n========== JSON ==========\n")
print(json.dumps(output, indent=2, ensure_ascii=False))