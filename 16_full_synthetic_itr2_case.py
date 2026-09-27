import json

from typesafe_sdk import (
    TypeSafeClient,
    Choice,
    Score,
    Noul,
    NoulCriteria,
)


# ============================================================
# EXPERIMENT 16
# FULL SYNTHETIC ITR-2 CASE
# ============================================================
#
# Purpose:
#
# Evaluate a synthetic ITR-2 return containing multiple
# independent issues across different schedules.
#
# The experiment combines:
#
#   1. Schedule S
#      Gross salary arithmetic
#
#   2. Schedule OS
#      Interest income reconciliation
#
#   3. Schedule CG
#      Capital-gain transaction arithmetic
#
#   4. Chapter VI-A / 80G
#      New-regime deduction conflict + evidence mismatch
#
#
# JEV primitives:
#
#   Choice -> classify the overall issue
#   Score  -> diagnose competing explanations
#   Noul   -> verify a specific proposition
#
#
# IMPORTANT:
#
# This is a synthetic research experiment.
# It is NOT a complete tax computation engine.
#
# Deterministic checks below intentionally cover only the
# specific relationships represented in this experiment.
#
# ============================================================


# ============================================================
# CBDT RULE REFERENCES USED IN THIS EXPERIMENT
# ============================================================

CBDT_RULES = {

    "SCHEDULE_S_RULE_22": {
        "rule_id": "ITR2_AY2026_27_RULE_22",
        "schedule": "Schedule S",
        "description": (
            "Gross Salary (1a + 1b + 1c + 1d + 1e + 1f) "
            "should be consistent with the sum of "
            "Sl. No. 1a + 1b + 1c + 1d + 1e + 1f."
        ),
    },

    "CHAPTER_VIA_RULE_342": {
        "rule_id": "ITR2_AY2026_27_RULE_342",
        "schedule": "Chapter VI-A",
        "description": (
            "If new tax regime is selected, deductions including "
            "80C, 80CCD(1B), 80D and 80G cannot be claimed."
        ),
    },
}


# ============================================================
# SYNTHETIC TAXPAYER
# ============================================================

taxpayer = {

    "taxpayer_id": "SYNTHETIC_001",

    "assessment_year": "2026-27",

    "tax_regime": "NEW",


    # --------------------------------------------------------
    # SCHEDULE S
    # --------------------------------------------------------

    "schedule_S": {

        "salary_components": {

            "1a_basic_salary":
                1200000,

            "1b_hra":
                550000,

            "1c_other_allowance":
                240000,

            "1d":
                0,

            "1e":
                0,

            "1f":
                0,
        },

        # Deliberately inconsistent
        "gross_salary":
            2090000,
    },


    # --------------------------------------------------------
    # SCHEDULE OS
    # --------------------------------------------------------

    "schedule_OS": {

        "interest_income":
            77000,
    },


    # --------------------------------------------------------
    # SCHEDULE CG
    # --------------------------------------------------------

    "schedule_CG": {

        "security":
            "INFOSYS",

        "quantity":
            100,

        "purchase_price":
            1400,

        "sale_price":
            1600,

        "declared_capital_gain":
            12000,
    },


    # --------------------------------------------------------
    # CHAPTER VI-A
    # --------------------------------------------------------

    "chapter_VIA": {

        "80C":
            150000,

        "80CCD_1B":
            50000,

        "80D":
            25000,

        "80G":
            75000,
    },
}


# ============================================================
# EXTERNAL EVIDENCE
# ============================================================

evidence = {

    # --------------------------------------------------------
    # FORM 16
    # --------------------------------------------------------

    "form16": {

        "basic_salary":
            1200000,

        "hra":
            480000,

        "other_allowance":
            240000,

        "gross_salary":
            1920000,
    },


    # --------------------------------------------------------
    # AIS
    # --------------------------------------------------------

    "ais": {

        "interest_income":
            95000,
    },


    # --------------------------------------------------------
    # BROKER
    # --------------------------------------------------------

    "broker": {

        "security":
            "INFOSYS",

        "quantity":
            100,

        "purchase_price":
            1400,

        "sale_price":
            1600,

        "purchase_date":
            "2025-04-10",

        "sale_date":
            "2025-09-20",
    },


    # --------------------------------------------------------
    # 80G RECEIPT
    # --------------------------------------------------------

    "donation_receipt": {

        "institution":
            "ABC Charitable Trust",

        "amount":
            50000,

        "transaction_reference":
            "TXN123456",
    },


    # --------------------------------------------------------
    # BANK
    # --------------------------------------------------------

    "bank": {

        "institution":
            "ABC Charitable Trust",

        "amount":
            50000,

        "transaction_reference":
            "TXN123456",
    },
}


# ============================================================
# DETERMINISTIC VALIDATION
# ============================================================

def validate_salary():

    components = (
        taxpayer["schedule_S"]["salary_components"]
    )

    calculated_gross = sum(
        components.values()
    )

    declared_gross = (
        taxpayer["schedule_S"]["gross_salary"]
    )

    form16_gross = (
        evidence["form16"]["gross_salary"]
    )

    return {

        "calculated_from_itr_components":
            calculated_gross,

        "itr_declared_gross":
            declared_gross,

        "itr_arithmetic_difference":
            declared_gross - calculated_gross,

        "itr_arithmetic_valid":
            declared_gross == calculated_gross,

        "form16_gross":
            form16_gross,

        "itr_vs_form16_difference":
            declared_gross - form16_gross,

        "itr_matches_form16":
            declared_gross == form16_gross,
    }


def validate_interest():

    ais_interest = (
        evidence["ais"]["interest_income"]
    )

    itr_interest = (
        taxpayer["schedule_OS"]["interest_income"]
    )

    return {

        "ais_interest_income":
            ais_interest,

        "itr_interest_income":
            itr_interest,

        "difference":
            itr_interest - ais_interest,

        "income_missing_from_itr":
            itr_interest < ais_interest,

        "valid":
            itr_interest == ais_interest,
    }


def validate_capital_gain():

    broker = evidence["broker"]

    expected_gain = (
        broker["sale_price"]
        - broker["purchase_price"]
    ) * broker["quantity"]

    declared_gain = (
        taxpayer["schedule_CG"]["declared_capital_gain"]
    )

    return {

        "security":
            taxpayer["schedule_CG"]["security"],

        "quantity":
            taxpayer["schedule_CG"]["quantity"],

        "purchase_price":
            taxpayer["schedule_CG"]["purchase_price"],

        "sale_price":
            taxpayer["schedule_CG"]["sale_price"],

        "expected_gain_from_synthetic_transaction":
            expected_gain,

        "declared_gain":
            declared_gain,

        "difference":
            declared_gain - expected_gain,

        "arithmetic_valid":
            declared_gain == expected_gain,
    }


def validate_chapter_via():

    deductions = (
        taxpayer["chapter_VIA"]
    )

    restricted_deductions = {
        "80C":
            deductions["80C"],

        "80CCD_1B":
            deductions["80CCD_1B"],

        "80D":
            deductions["80D"],

        "80G":
            deductions["80G"],
    }

    non_zero_conflicts = {
        key: value
        for key, value
        in restricted_deductions.items()
        if value > 0
    }

    return {

        "tax_regime":
            taxpayer["tax_regime"],

        "claimed_deductions":
            deductions,

        "restricted_under_experiment_rule":
            non_zero_conflicts,

        "conflict_detected":
            (
                taxpayer["tax_regime"] == "NEW"
                and len(non_zero_conflicts) > 0
            ),

        "donation_receipt_amount":
            evidence["donation_receipt"]["amount"],

        "bank_donation_amount":
            evidence["bank"]["amount"],

        "itr_80G_amount":
            deductions["80G"],

        "80G_evidence_difference":
            (
                deductions["80G"]
                - evidence["donation_receipt"]["amount"]
            ),

        "80G_evidence_supported":
            (
                deductions["80G"]
                == evidence["donation_receipt"]["amount"]
                == evidence["bank"]["amount"]
            ),
    }


# ============================================================
# RUN DETERMINISTIC VALIDATION
# ============================================================

salary_validation = validate_salary()

interest_validation = validate_interest()

capital_gain_validation = validate_capital_gain()

chapter_via_validation = validate_chapter_via()


# ============================================================
# FULL CASE
# ============================================================

full_case = {

    "assessment_year":
        taxpayer["assessment_year"],

    "tax_regime":
        taxpayer["tax_regime"],

    "itr": {

        "schedule_S":
            taxpayer["schedule_S"],

        "schedule_OS":
            taxpayer["schedule_OS"],

        "schedule_CG":
            taxpayer["schedule_CG"],

        "chapter_VIA":
            taxpayer["chapter_VIA"],
    },

    "evidence":
        evidence,

    "deterministic_validation": {

        "schedule_S":
            salary_validation,

        "schedule_OS":
            interest_validation,

        "schedule_CG":
            capital_gain_validation,

        "chapter_VIA":
            chapter_via_validation,
    },

    "applicable_cbdt_rules":
        CBDT_RULES,
}


# ============================================================
# JEV QUESTIONS
# ============================================================

classification_question = Choice(

    instructions=(
        "Analyze the complete synthetic ITR-2 case. "
        "Identify the dominant overall validation state. "
        "Use the supplied deterministic checks, evidence, "
        "and explicitly supplied CBDT rules. "
        "Do not invent additional tax rules."
    ),

    criteria={

        "NO_MATERIAL_DISCREPANCY":
            (
                "The supplied ITR data is materially consistent "
                "with the supplied evidence and rules."
            ),

        "SALARY_DISCREPANCY":
            (
                "The dominant issue is a Schedule S salary "
                "discrepancy."
            ),

        "INTEREST_INCOME_DISCREPANCY":
            (
                "The dominant issue is a Schedule OS "
                "interest-income discrepancy."
            ),

        "CAPITAL_GAIN_DISCREPANCY":
            (
                "The dominant issue is a Schedule CG "
                "capital-gain discrepancy."
            ),

        "CHAPTER_VIA_CONFLICT":
            (
                "The dominant issue is a Chapter VI-A "
                "tax-regime/deduction conflict."
            ),

        "MULTIPLE_DISCREPANCIES":
            (
                "Multiple independent discrepancies are "
                "present across the supplied schedules."
            ),
    },
)


diagnosis_question = Score(

    instructions=(
        "Analyze the supplied synthetic ITR-2 case and "
        "diagnose the possible sources of inconsistency. "
        "Use the deterministic validation and evidence as "
        "important signals. Distinguish arithmetic errors, "
        "source reconciliation differences, and rule conflicts."
    ),

    criteria=[

        (
            "The complete return is materially consistent "
            "with the supplied evidence and rules."
        ),

        (
            "The primary issue is a Schedule S "
            "salary arithmetic or component discrepancy."
        ),

        (
            "The primary issue is missing interest income "
            "relative to AIS."
        ),

        (
            "The primary issue is a capital-gain calculation "
            "or data-entry discrepancy."
        ),

        (
            "The primary issue is a Chapter VI-A deduction "
            "conflict with the selected tax regime."
        ),

        (
            "Multiple independent discrepancies exist "
            "and cannot be represented by a single issue."
        ),
    ],
)


verification_question = Noul(

    instructions=(
        "Verify the following proposition using only the "
        "supplied ITR data, external evidence, deterministic "
        "validation results, and explicitly supplied CBDT rules:"
        "\n\n"
        "The complete synthetic ITR-2 case is fully supported "
        "by the supplied evidence and satisfies the explicitly "
        "supplied validation rules."
    ),

    criteria=NoulCriteria(

        true=(
            "The proposition is supported by the supplied "
            "data and rules."
        ),

        false=(
            "The proposition is not supported by the supplied "
            "data and rules."
        ),
    ),
)


# ============================================================
# EXECUTE SYSTEM ONE
# ============================================================

print(
    "\nRunning full synthetic ITR-2 JEV analysis..."
)


with TypeSafeClient() as client:

    response = client.system_one(

        state={
            "synthetic_itr2_case":
                full_case,
        },

        questions={

            "classification":
                classification_question,

            "diagnosis":
                diagnosis_question,

            "overall_support":
                verification_question,
        },
    )


# ============================================================
# SERIALIZATION HELPER
# ============================================================

def dump_answer(answer):

    if hasattr(answer, "model_dump"):
        return answer.model_dump()

    return str(answer)


# ============================================================
# EXTRACT ANSWERS
# ============================================================

classification_result = dump_answer(
    response.answers["classification"]
)

diagnosis_result = dump_answer(
    response.answers["diagnosis"]
)

verification_result = dump_answer(
    response.answers["overall_support"]
)


# ============================================================
# DETERMINISTIC ISSUE SUMMARY
# ============================================================

issues = []


# Schedule S

if not salary_validation["itr_arithmetic_valid"]:

    issues.append({
        "schedule": "Schedule S",
        "issue": "GROSS_SALARY_ARITHMETIC_MISMATCH",
        "difference":
            salary_validation[
                "itr_arithmetic_difference"
            ],
    })


if not salary_validation["itr_matches_form16"]:

    issues.append({
        "schedule": "Schedule S",
        "issue": "FORM16_ITR_SALARY_DIFFERENCE",
        "difference":
            salary_validation[
                "itr_vs_form16_difference"
            ],
    })


# Schedule OS

if not interest_validation["valid"]:

    issues.append({
        "schedule": "Schedule OS",
        "issue": "INTEREST_INCOME_DIFFERENCE",
        "difference":
            interest_validation["difference"],
    })


# Schedule CG

if not capital_gain_validation["arithmetic_valid"]:

    issues.append({
        "schedule": "Schedule CG",
        "issue": "CAPITAL_GAIN_ARITHMETIC_MISMATCH",
        "difference":
            capital_gain_validation["difference"],
    })


# Chapter VI-A

if chapter_via_validation["conflict_detected"]:

    issues.append({
        "schedule": "Chapter VI-A",
        "issue": "NEW_REGIME_DEDUCTION_CONFLICT",
        "deductions":
            chapter_via_validation[
                "restricted_under_experiment_rule"
            ],
    })


if not chapter_via_validation["80G_evidence_supported"]:

    issues.append({
        "schedule": "80G",
        "issue": "DONATION_EVIDENCE_AMOUNT_MISMATCH",
        "difference":
            chapter_via_validation[
                "80G_evidence_difference"
            ],
    })


# ============================================================
# OVERALL DETERMINISTIC STATUS
# ============================================================

if len(issues) == 0:

    deterministic_status = (
        "NO_MATERIAL_DISCREPANCY"
    )

elif len(issues) == 1:

    deterministic_status = (
        "SINGLE_DISCREPANCY"
    )

else:

    deterministic_status = (
        "MULTIPLE_DISCREPANCIES"
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

result = {

    "experiment":
        "Full Synthetic ITR-2 Case",

    "taxpayer_id":
        taxpayer["taxpayer_id"],

    "assessment_year":
        taxpayer["assessment_year"],

    "deterministic": {

        "status":
            deterministic_status,

        "issue_count":
            len(issues),

        "issues":
            issues,

        "schedule_S":
            salary_validation,

        "schedule_OS":
            interest_validation,

        "schedule_CG":
            capital_gain_validation,

        "chapter_VIA":
            chapter_via_validation,
    },

    "jev": {

        "classification":
            classification_result,

        "diagnosis":
            diagnosis_result,

        "overall_support":
            verification_result,
    },
}


# ============================================================
# PRINT
# ============================================================

print(
    "\n========== JSON ==========\n"
)

print(
    json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    )
)