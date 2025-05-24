import json
import openai
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
# === CONFIGURATION ===
PROGRAM_FILES = {
    'informal': os.path.join('prompts', 'informal_mitigation.json'),
    'affordable': os.path.join('prompts', 'affordable_mitigation.json')
}

AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_API_VERSION = "2023-05-15"
client = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version="2024-02-01"
)

REJECT_CATEGORIES = [
    "Bureau or Credit Score", "Customer Profile", "Eligibility Issue", "FOIR Enhancement",
    "Business Vintage or Work Experience","Business Setup", "Age Deviation", "Overleveraged Profile",
    "Banking norms", "Collateral or Property", "BT norms", "ITR Gap", "Personal Discussion",
    "Loan Amount breach", "Geolimit", "BT Vintage", "Hunter Negative", "Turnover Decline", "FI Negative"
]


def categorize_reason_with_gpt(reason: str) -> str:

    prompt = f"""

Act as AI-Powered regional Business Head experience with deep experience in housing finance industry.

You specialize in diagnosing and classifying business logic behind loan application rejections.
Your task is to categorize the following **reject reason** into only one of the predefined **reject categories**

Think deeply -- at least 10 times about true root cause behind the rejection.
Reject Reason: "{reason}"

Categories:
{', '.join(REJECT_CATEGORIES)}

Return only the exact matching category name-- nothing else
    """

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

def match_program(program: str, reason: str):
    """
    Filters mitigant data based on the GPT-predicted category.
    """
    predicted_category = categorize_reason_with_gpt(reason)

    if(program.lower() == 'informal'):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        uncle_folder = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "prompts")
        file = os.path.join(uncle_folder, "Mitigation.txt")
        with open(file, 'r', encoding='utf-8') as f:
            res = json.load(f)
            return res
    
    # print(reason)
    file_path = PROGRAM_FILES.get(program.lower())
    if not file_path:
        raise ValueError(f"Unknown program: {program}")

    with open(file_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    filtered = [
        {
            "Reject Category": r.get("Reject Category", ""),
            "Reject Reasons": r.get("Reject Reasons", ""),
            "List of Mitigants": r.get("List of Mitigants ", ""),
            "Quantitative Measures \nMitigates": r.get("Quantitative measures, \nMitigates", "")
        }
        for r in records
        if r.get("Reject Category", "").strip() == predicted_category
    ]
    # print(predicted_category)
    # print(filtered)
    if len(filtered) != 0 :
        filtered = filtered
    else:
        filtered = predicted_category

    # print(filtered)
    return f"""
✅ Your Mission:
Compare the user query against the reject reason fields from the provided JSON data.

If a match is found, respond only with the mitigants and quantitative measures in a generalized, future-focused format—no assumptions, no specifics.

The provided mitigants and measures are based on previous cases and may not apply universally.

The response should guide the applicant on possible actions but not assume they will work for all cases.

📋 Strict Rules to Follow
Importartant Rule:
 - When a reject category is provided but reject reason is missing or not clear, the system should:
 - identify all related reject reasons under given category.
 - aggregate all mitigants and qaulititive measures associated with those reasons.
 - Present the combined list of mitigants and measures are generalized, non-case-specific guidance.

1️⃣ if Reject reason are contextually similar and within the same category

Must combine mitigants and quantitive measure from **all related reasons within that category**
Consider the reject reason matched if it **partially matched or share context** with existing one in the same category
Ensure the response includes **deduplicated** and **generalized** mitigants from merged group.
Never include mitigants from a different reject category.


2️⃣ Provide Only Mitigants & Quantitative Measures
DO NOT mention the reject category or reason unless the user explicitly asks.

If the query matches a previous rejection case, respond with potential mitigants framed as considerations, not solutions.

3️⃣ Keep It General & Future-Focused
Never assume the cause of rejection.

Use only action-based, forward-looking phrasing:

✅ "Identify the reason..."

✅ "Provide documentation..."

✅ "Clarify the circumstances..."

❌ Avoid phrases like "issue identified" or references to past approvals.

4️⃣ Include Approval or Program If Stated
If mitigants list any approval dependency (e.g., NCM approval, additional validations), it must be included.

If a Program is mentioned (e.g., Cash Salaried Program), it must be referenced in the response.

Keep the response neutral and framed as possible considerations.

5️⃣ Use Future-Tense Action Verbs
Always frame suggested actions as things to be considered or done in the future:

✅ "Identify..."

✅ "Provide..."

✅ "Ensure..."

✅ "Maintain..."

6️⃣ Convert Numbers into Qualitative Terms
Replace numeric values with descriptive terms:

ROI percentages → "charged premium ROI"

Loan tenure → "longer tenure"

FOIR → "moderate FOIR"

LTV → "restricted LTV"

7️⃣ Remain Product-Agnostic
If specific product types are mentioned (e.g., "home extension loan"), generalize:

✅ "Consider alternative loan options."

8️⃣ Generalize Based on Previous Cases
Present previous mitigants as potential next steps, never final answers.

Emphasize that each case is unique and subject to individual assessment.

9️⃣ Never Mention Reject Category or Reason (Unless Asked)
Only reference mitigants and measures—do not state category or reason unless explicitly asked by the user.

✅ Before Responding, Double-Check:
✔ Is the response general, not case-specific?
✔ Are combined mitigants only from the same reject category?
✔ Are all suggestions framed as guidance (e.g., "Provide," "Ensure")?
✔ Are all numbers converted into quantitative terms? for both mitigants and qauntitive measure
✔ Are mitigants and measure merged for same category?
✔ Have you avoided assuming outcome or cause?
✔ Are approval/program flags mentioned, if present in mitigants?
✔ Is the language neutral, non-committal, and future-oriented?
✔ Have you avoided personal, familial, or relational references?
✔ If the profile is "Negative" under the specified program but marked "Caution" or "Not Applicable" under another, respond with: "Not eligible under program, consider evaluating under alternate_program." Don't suggest this as MItigants as customer not eligible

🔹 This ensures responses are:
Guidance-oriented

Neutral and non-prescriptive

Compliant and scalable for future rejection scenarios

Only refer to the below reject reasons and categories to provide mitigants and quantitative measures:

----------------------------------
{filtered}

----------------------------------
At the end of the response, include this statement verbatim:

Listed measures for credit mitigants are exhaustive and limited to Informal cases, they may vary case to case basis. However, it is advisable to refer these mitigants before file login. Measures for Prime is in cooking stage.
"""


