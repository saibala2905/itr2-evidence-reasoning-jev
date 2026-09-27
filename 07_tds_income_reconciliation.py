import os
import json

from typesafe_sdk import TypeSafeClient, Noul, NoulCriteria


# =========================================================
# Client
# =========================================================

client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# =========================================================
# Source evidence
# =========================================================

source = {
    "payer": "ABC Bank Ltd",
    "income_type": "Interest Income",
    "interest_income": 80_000,
    "tds_deducted": 8_000,
}


# =========================================================
# ITR declaration
# =========================================================

itr = {
    "interest_income": 0,
    "tds_claimed": 8_000,
}


# =========================================================
# Noul questions
# =========================================================

questions = {

    "income_supported": Noul(
        instructions={
            "source": source,
            "itr": itr,
            "claim": (
                "The ITR declares interest income of "
                "₹0 even though the source reports ₹80,000."
            ),
        },
        criteria=NoulCriteria(
            true=(
                "The ITR income declaration is not supported "
                "by the source evidence."
            ),
            false=(
                "The ITR income declaration is supported "
                "by the source evidence."
            ),
        ),
    ),

    "tds_supported": Noul(
        instructions={
            "source": source,
            "itr": itr,
            "claim": (
                "The ITR claims ₹8,000 of TDS corresponding "
                "to the source document."
            ),
        },
        criteria=NoulCriteria(
            true=(
                "The claimed TDS is not supported by the source."
            ),
            false=(
                "The claimed TDS is supported by the source."
            ),
        ),
    ),

    "tds_income_consistent": Noul(
        instructions={
            "source": source,
            "itr": itr,
            "claim": (
                "The TDS claim and corresponding income declaration "
                "are consistent with each other."
            ),
        },
        criteria=NoulCriteria(
            true=(
                "The TDS claim and corresponding income declaration "
                "are inconsistent."
            ),
            false=(
                "The TDS claim and corresponding income declaration "
                "are consistent."
            ),
        ),
    ),
}


# =========================================================
# Run JEV
# =========================================================

result = client.system_one(
    state={
        "source": source,
        "itr": itr,
    },
    questions=questions,
)


# =========================================================
# Deterministic validation
# =========================================================

deterministic = {
    "source_income": source["interest_income"],
    "itr_income": itr["interest_income"],
    "source_tds": source["tds_deducted"],
    "itr_tds": itr["tds_claimed"],
    "income_missing": (
        source["interest_income"] > 0
        and itr["interest_income"] == 0
    ),
    "tds_supported": (
        source["tds_deducted"] == itr["tds_claimed"]
    ),
}


# =========================================================
# JSON
# =========================================================

answers = {}

for name, answer in result.answers.items():
    answers[name] = (
        answer.model_dump()
        if hasattr(answer, "model_dump")
        else str(answer)
    )


output = {
    "source": source,
    "itr": itr,
    "deterministic_validation": deterministic,
    "jev": answers,
}


print("\n========== JSON ==========\n")
print(json.dumps(output, indent=2, ensure_ascii=False))