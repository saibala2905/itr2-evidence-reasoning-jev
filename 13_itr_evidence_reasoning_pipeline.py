import json

from typesafe_sdk import (
    TypeSafeClient,
    Choice,
    Score,
    Noul,
)


# ============================================================
# HELPERS
# ============================================================

def dump_answer(answer):
    """
    Convert a TypeSafe answer object into JSON-serializable data.
    """
    if hasattr(answer, "model_dump"):
        return answer.model_dump()

    return str(answer)


def dump_response_answer(response, key):
    """
    Extract one named answer from response.answers.
    """
    return dump_answer(response.answers[key])


# ============================================================
# TAXPAYER DATA
# ============================================================

taxpayer = {
    "taxpayer_id": "TEST_001",

    "salary": {
        "form16": {
            "basic_salary": 1200000,
            "hra": 480000,
            "special_allowance": 240000,
            "gross_salary": 1920000,
        },

        "itr": {
            "basic_salary": 1200000,
            "hra": 550000,
            "special_allowance": 240000,
            "gross_salary": 2090000,
        },
    },

    "interest": {
        "ais": {
            "interest_income": 95000,
        },

        "itr": {
            "interest_income": 77000,
        },
    },

    "donation": {
        "receipt": {
            "institution": "ABC Charitable Trust",
            "amount": 50000,
            "transaction_reference": "TXN123456",
        },

        "bank": {
            "institution": "ABC Charitable Trust",
            "amount": 50000,
            "transaction_reference": "TXN123456",
        },

        "itr": {
            "institution": "ABC Charitable Trust",
            "amount": 75000,
            "transaction_reference": "TXN123456",
        },
    },
}


# ============================================================
# DETERMINISTIC VALIDATION
# ============================================================

def validate_salary(data):
    form16 = data["form16"]
    itr = data["itr"]

    expected_gross_from_form16 = (
        form16["basic_salary"]
        + form16["hra"]
        + form16["special_allowance"]
    )

    expected_gross_from_itr_components = (
        itr["basic_salary"]
        + itr["hra"]
        + itr["special_allowance"]
    )

    return {
        "form16_gross": form16["gross_salary"],
        "itr_gross": itr["gross_salary"],

        "expected_gross_from_form16_components":
            expected_gross_from_form16,

        "expected_gross_from_itr_components":
            expected_gross_from_itr_components,

        "itr_gross_arithmetic_valid":
            itr["gross_salary"]
            == expected_gross_from_itr_components,

        "itr_vs_form16_gross_difference":
            itr["gross_salary"]
            - form16["gross_salary"],

        "hra_difference":
            itr["hra"] - form16["hra"],

        "hra_matches_form16":
            itr["hra"] == form16["hra"],

        "salary_materially_consistent":
            (
                itr["gross_salary"]
                == form16["gross_salary"]
                and itr["hra"]
                == form16["hra"]
            ),
    }


def validate_interest(data):
    ais_income = data["ais"]["interest_income"]
    itr_income = data["itr"]["interest_income"]

    return {
        "ais_interest_income": ais_income,
        "itr_interest_income": itr_income,

        "difference":
            itr_income - ais_income,

        "missing_from_itr":
            ais_income - itr_income,

        "income_missing":
            itr_income < ais_income,

        "valid":
            itr_income == ais_income,
    }


def validate_donation(data):
    receipt = data["receipt"]
    bank = data["bank"]
    itr = data["itr"]

    return {
        "receipt_amount": receipt["amount"],
        "bank_amount": bank["amount"],
        "itr_amount": itr["amount"],

        "receipt_bank_match":
            receipt["amount"] == bank["amount"],

        "transaction_reference_matches":
            (
                receipt["transaction_reference"]
                == bank["transaction_reference"]
                == itr["transaction_reference"]
            ),

        "itr_amount_difference":
            itr["amount"] - receipt["amount"],

        "valid":
            (
                receipt["amount"]
                == bank["amount"]
                == itr["amount"]
            ),
    }


salary_validation = validate_salary(
    taxpayer["salary"]
)

interest_validation = validate_interest(
    taxpayer["interest"]
)

donation_validation = validate_donation(
    taxpayer["donation"]
)


# ============================================================
# PREPARE CASES FOR JEV
# ============================================================

salary_case = {
    "source": taxpayer["salary"]["form16"],
    "itr": taxpayer["salary"]["itr"],
    "deterministic_validation": salary_validation,
}


interest_case = {
    "source": taxpayer["interest"]["ais"],
    "itr": taxpayer["interest"]["itr"],
    "deterministic_validation": interest_validation,
}


donation_case = {
    "receipt": taxpayer["donation"]["receipt"],
    "bank": taxpayer["donation"]["bank"],
    "itr": taxpayer["donation"]["itr"],
    "deterministic_validation": donation_validation,
}


# ============================================================
# JEV — SALARY
# ============================================================

salary_state = {
    "schedule": "Schedule S",
    "case": salary_case,
}


salary_questions = {

    "classification": Choice(
        instructions=(
            "Classify the salary discrepancy using the supplied "
            "Form 16, ITR data, and deterministic validation."
        ),

        criteria={
            "NO_MATERIAL_DISCREPANCY":
                "The salary information is materially consistent.",

            "COMPONENT_MISMATCH":
                "One or more salary components differ between "
                "the source evidence and ITR.",

            "GROSS_SALARY_MISMATCH":
                "The gross salary declared in the ITR differs "
                "from the source-supported gross salary.",

            "ARITHMETIC_ERROR":
                "The gross salary does not equal the sum of "
                "the applicable salary components.",

            "OTHER":
                "Another salary discrepancy is present.",
        },
    ),

    "diagnosis": Score(
        instructions=(
            "Determine the most plausible explanation for the "
            "salary discrepancy."
        ),

        criteria=[
            "The salary information is fully consistent.",

            "The HRA component appears to be incorrect.",

            "The gross salary appears to be incorrect.",

            "The gross salary contains an arithmetic or "
            "data-entry error.",

            "The discrepancy may be caused by a source-record "
            "difference.",

            "The discrepancy cannot be reliably explained from "
            "the supplied evidence.",
        ],
    ),

    "evidence_supported": Noul(
        instructions=(
            "Determine whether the gross salary declared in the "
            "ITR is fully supported by the supplied Form 16 "
            "salary components."
        ),
    ),
}


# ============================================================
# JEV — INTEREST
# ============================================================

interest_state = {
    "schedule": "Schedule OS",
    "case": interest_case,
}


interest_questions = {

    "classification": Choice(
        instructions=(
            "Classify the interest-income discrepancy using "
            "the AIS, ITR and deterministic validation."
        ),

        criteria={
            "NO_MATERIAL_DISCREPANCY":
                "AIS and ITR interest income are consistent.",

            "INCOME_OMITTED":
                "AIS reports interest income that is not fully "
                "reflected in the ITR.",

            "SOURCE_MISMATCH":
                "The source records themselves appear inconsistent.",

            "DATA_ENTRY_ERROR":
                "The ITR amount appears to contain a "
                "transcription or data-entry error.",

            "DUPLICATE_ENTRY":
                "The records may contain duplicate or "
                "overlapping income.",

            "OTHER":
                "Another interest-income discrepancy exists.",
        },
    ),

    "diagnosis": Score(
        instructions=(
            "Determine the most plausible explanation for the "
            "difference between AIS and ITR interest income."
        ),

        criteria=[
            "The ITR interest income is fully supported.",

            "One or more interest-income sources are missing "
            "from the ITR.",

            "AIS income is not reflected in the ITR.",

            "The AIS and source records differ.",

            "The ITR contains a transcription or data-entry error.",

            "The records may be duplicated or overlapping.",
        ],
    ),

    "evidence_supported": Noul(
        instructions=(
            "Determine whether the interest income reported "
            "in the ITR fully reflects the AIS amount."
        ),
    ),
}


# ============================================================
# JEV — DONATION
# ============================================================

donation_state = {
    "schedule": "Schedule 80G",
    "case": donation_case,
}


donation_questions = {

    "classification": Choice(
        instructions=(
            "Classify the donation discrepancy using the "
            "receipt, bank transaction, ITR and deterministic "
            "validation."
        ),

        criteria={
            "SUPPORTED":
                "The donation amount and transaction are "
                "supported by the evidence.",

            "AMOUNT_MISMATCH":
                "The ITR donation amount differs from the "
                "receipt or bank evidence.",

            "TRANSACTION_MISMATCH":
                "The transaction reference or beneficiary differs.",

            "MISSING_EVIDENCE":
                "Required supporting evidence is absent.",

            "OTHER":
                "Another donation discrepancy exists.",
        },
    ),

    "diagnosis": Score(
        instructions=(
            "Determine the most plausible explanation for "
            "the donation discrepancy."
        ),

        criteria=[
            "The donation is fully supported by receipt "
            "and bank evidence.",

            "The donation amount declared in the ITR is incorrect.",

            "The transaction reference or beneficiary is incorrect.",

            "Supporting evidence is missing.",

            "The ITR contains a data-entry error.",

            "The transaction may be duplicated.",
        ],
    ),

    "evidence_supported": Noul(
        instructions=(
            "Determine whether the donation amount claimed "
            "in the ITR is fully supported by the receipt "
            "and bank evidence."
        ),
    ),
}


# ============================================================
# EXECUTE SYSTEM ONE
# ============================================================

print("\nRunning salary JEV analysis...")

with TypeSafeClient() as client:

    salary_response = client.system_one(
        state=salary_state,
        questions=salary_questions,
    )

    print("Running interest JEV analysis...")

    interest_response = client.system_one(
        state=interest_state,
        questions=interest_questions,
    )

    print("Running donation JEV analysis...")

    donation_response = client.system_one(
        state=donation_state,
        questions=donation_questions,
    )


# ============================================================
# EXTRACT JEV RESULTS
# ============================================================

salary_jev = {
    "classification":
        dump_response_answer(
            salary_response,
            "classification"
        ),

    "diagnosis":
        dump_response_answer(
            salary_response,
            "diagnosis"
        ),

    "evidence_supported":
        dump_response_answer(
            salary_response,
            "evidence_supported"
        ),
}


interest_jev = {
    "classification":
        dump_response_answer(
            interest_response,
            "classification"
        ),

    "diagnosis":
        dump_response_answer(
            interest_response,
            "diagnosis"
        ),

    "evidence_supported":
        dump_response_answer(
            interest_response,
            "evidence_supported"
        ),
}


donation_jev = {
    "classification":
        dump_response_answer(
            donation_response,
            "classification"
        ),

    "diagnosis":
        dump_response_answer(
            donation_response,
            "diagnosis"
        ),

    "evidence_supported":
        dump_response_answer(
            donation_response,
            "evidence_supported"
        ),
}


# ============================================================
# OVERALL STATUS
# ============================================================

issues = []

if not salary_validation["salary_materially_consistent"]:
    issues.append("SALARY")

if not interest_validation["valid"]:
    issues.append("INTEREST_INCOME")

if not donation_validation["valid"]:
    issues.append("DONATION")


if len(issues) == 0:
    overall_status = "NO_MATERIAL_DISCREPANCY"

elif len(issues) == 1:
    overall_status = "REVIEW_REQUIRED"

else:
    overall_status = "MULTIPLE_ISSUES_REVIEW_REQUIRED"


# ============================================================
# FINAL OUTPUT
# ============================================================

result = {

    "taxpayer_id":
        taxpayer["taxpayer_id"],

    "deterministic_validation": {

        "salary":
            salary_validation,

        "interest":
            interest_validation,

        "donation":
            donation_validation,
    },

    "jev": {

        "salary":
            salary_jev,

        "interest":
            interest_jev,

        "donation":
            donation_jev,
    },

    "overall": {

        "status":
            overall_status,

        "issues_detected":
            issues,

        "issue_count":
            len(issues),
    },
}


print("\n========== JSON ==========\n")

print(
    json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    )
)