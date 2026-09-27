import os
import json

from typesafe_sdk import TypeSafeClient, Choice


# ---------------------------------------------------------
# TypeSafe / JEV client
# ---------------------------------------------------------

client = TypeSafeClient(
    api_key=os.environ["TYPESAFE_API_KEY"],
    model="jev-latest",
    timeout=30.0,
)


# ---------------------------------------------------------
# Document to classify
# ---------------------------------------------------------

document = """
FORM 16

Employer: ABC Technologies Pvt Ltd
Employee Name: Saibala Sundram

Assessment Year: 2026-27

Basic Salary: Rs. 12,00,000
House Rent Allowance: Rs. 4,80,000
Special Allowance: Rs. 2,40,000

Gross Salary: Rs. 19,20,000

Tax Deducted at Source (TDS): Rs. 2,85,000

Employer TAN: BLRA12345A
"""


# ---------------------------------------------------------
# Choice question
# ---------------------------------------------------------

document_type_question = Choice(
    instructions={
        "document": document,
        "task": (
            "Identify the type of Indian income-tax document "
            "represented by the supplied document."
        ),
    },

    criteria={
        "FORM_16": (
            "A salary/TDS certificate issued by an employer to an employee, "
            "typically containing salary components, exemptions, deductions "
            "and tax deducted at source."
        ),

        "AIS": (
            "An Annual Information Statement containing information reported "
            "to the income-tax department, such as salary, interest, dividends, "
            "securities transactions, TDS/TCS and other reported information."
        ),

        "FORM_26AS": (
            "A tax credit statement containing information such as TDS, TCS, "
            "advance tax, self-assessment tax and other tax-related credits."
        ),

        "BROKER_STATEMENT": (
            "A statement from a stock broker or investment platform containing "
            "securities transactions, purchases, sales, quantities, prices, "
            "capital gains or related investment information."
        ),

        "BANK_STATEMENT": (
            "A statement issued by a bank containing account transactions, "
            "credits, debits, balances, interest or other banking activity."
        ),

        "HOME_LOAN_CERTIFICATE": (
            "A certificate issued by a lender containing housing-loan details, "
            "such as principal repayment, interest paid and loan information."
        ),

        "DONATION_RECEIPT": (
            "A receipt issued by a charitable or eligible institution "
            "documenting a donation or contribution."
        ),

        "OTHER": (
            "A document that does not match any of the other defined "
            "Indian income-tax document categories."
        ),
    },
)


# ---------------------------------------------------------
# Run System One
# ---------------------------------------------------------

result = client.system_one(
    state={
        "document": document,
    },
    questions={
        "document_classification": document_type_question,
    },
)


# ---------------------------------------------------------
# Print normal result
# ---------------------------------------------------------

print("\n========== RESULT ==========\n")

for name, answer in result.answers.items():
    print(name, "=>", answer)


# ---------------------------------------------------------
# Convert result to JSON
# ---------------------------------------------------------

json_output = {}

for name, answer in result.answers.items():

    if hasattr(answer, "model_dump"):
        json_output[name] = answer.model_dump()

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