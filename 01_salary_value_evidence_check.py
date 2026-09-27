# 01_salary_evidence_noul.py

import os

from typesafe_sdk import (
    TypeSafeClient,
    Noul,
    NoulCriteria,
)


client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


form16 = """
FORM 16

Employer: ABC Technologies Pvt Ltd
Assessment Year: 2026-27

Basic Salary: Rs. 12,00,000
House Rent Allowance: Rs. 4,80,000
Special Allowance: Rs. 2,40,000

Gross Salary: Rs. 19,20,000
"""


itr = {
    "basic_salary": 12_00_000,
    "hra": 4_80_000,
    "special_allowance": 2_40_000,
    "gross_salary": 21_00_000,
}


questions = {

    "basic_salary_supported": Noul(
        instructions={
            "source": form16,
            "itr_value": itr["basic_salary"],
        },
        criteria=NoulCriteria(
            true="The claimed basic salary is not supported by the source.",
            false="The claimed basic salary is supported by the source.",
        ),
    ),

    "hra_supported": Noul(
        instructions={
            "source": form16,
            "itr_value": itr["hra"],
        },
        criteria=NoulCriteria(
            true="The claimed HRA is not supported by the source.",
            false="The claimed HRA is supported by the source.",
        ),
    ),

    "gross_salary_supported": Noul(
        instructions={
            "source": form16,
            "itr_value": itr["gross_salary"],
        },
        criteria=NoulCriteria(
            true="The claimed gross salary is not supported by the source.",
            false="The claimed gross salary is supported by the source.",
        ),
    ),
}


result = client.system_one(
    state={
        "form16": form16,
        "itr2_schedule_s": itr,
    },
    questions=questions,
)


for name, answer in result.answers.items():
    print(f"{name}: {answer.noul:.4f}")