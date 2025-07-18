import json
import openai
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
# === CONFIGURATION ===
PROGRAM_FILES = {
    'informal': os.path.join('prompts', 'informal_mitigation.json'),
    'affordable': os.path.join('prompts', 'affordable_mitigation.json'),
    'prime': os.path.join('prompts', 'prime_mitigation.json')
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
    "Business Vintage or Work Experience", "Business Setup", "Age Deviation", "Overleveraged Profile",
    "Banking norms", "Collateral or Property", "BT norms", "ITR Gap", "Personal Discussion",
    "Loan Amount breach", "Geolimit", "BT Vintage", "Hunter Negative", "Turnover Decline", "FI Negative"
]
def evaluate_customer_profile_with_gpt(program : str,reason: str) -> str:
    file_path = 'prompts/non_targeted_profile.txt'

    with open(file_path, 'r', encoding='utf-8') as f:
        profile_data = f.read()

    prompt = f"""
## Credit Policy Analysis Prompt – Housing Loans

You are an expert in credit policy analysis for housing loans.

You are provided with a list of **non-targeted customer profiles** across different loan programs:
- **Prime**  
- **Affordable**  
- **Informal**

### Input Variables:
- **Program**: `{program}`  
- **Reject Reason**: `{reason}`  
- **Data (non_targeted_profiles.txt)**:  
-  {profile_data}

---
---

### Your Task:

Analyze whether the **reject reason matches any non-targeted profile** for:

- The specified program (`{program}`), **OR**
- **All three programs** (Prime, Affordable, Informal)

---

### Decision Logic:

Respond with one of the following **three** responses based on the conditions below:

1. **If the reject reason matches a profile that is marked "Negative"**:
 - In the **specified program**, **AND**
 - In **all other programs** as well (i.e., Negative across all),
 
 Respond with:
 > **"This case does not fall under any eligible profile segment. We may not be able to process this case."**

2. **If the reject reason does not match any non-targeted profile**, or the profile is marked:
 - As **"Caution"** or **"Not Applicable"** in **any program**,
 
 Respond with:
 > **"Proceed with mitigant filtering"**

3. **If the profile is marked as "Negative" in the specified program**, but is **"Caution"** or **"Not Applicable"** in any of the **other two programs**,  
 Respond with:
 > **"This profile is not eligible under the {program} program. However, it may be considered under another program with a 'Caution' or 'Not Applicable' flag. Please explore alternate program fitment."**

---

### Important Notes:

- Be **strict and precise** in your interpretation.
- Always provide **only one** of the three valid responses:

1. **"This case does not fall under any eligible profile segment. We may not be able to process this case."**  
2. **"Proceed with mitigant filtering"**  
3. **"This profile is not eligible under the {program} program. However, it may be considered under another program with a 'Caution' or 'Not Applicable' flag. Please explore alternate program fitment."**

"""

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

import re
def categorize_reason_with_gpt(reason: str) -> str:

    prompt = f"""

    Act as AI-Powered regional Business Head experience with deep experience in housing finance industry.

    You specialize in diagnosing and classifying business logic behind loan application rejections.
    Your task is to categorize the following **reject reason** into only one of the predefined **reject categories**
    
    Think deeply -- at least 100 times about true root cause behind the rejection.it's very cruisal.
    Reject Reason: "{reason}"

    Categories:
    {', '.join(REJECT_CATEGORIES)}
   
    Output response:
    Return a JSON object with the following format:
    {{
        "categories": ["Category1", "Category2"]
    }}
    If none match, return:
    {{
        "categories": []
    }}
    
    """

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    content = response.choices[0].message.content.strip()
    # Remove Markdown-style code block if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.MULTILINE)

    # print(content)
    try:
        result = json.loads(content)
        if isinstance(result, dict) and "categories" in result and isinstance(result["categories"], list):
            print(result)
            return result
        else:
            # logging.warning("Unexpected response structure: %s", content)
            return {"categories": []}
    except json.JSONDecodeError:
        # logging.error("JSON decoding failed. Raw content: %s", content)
        return {"categories": []}

    # return response.choices[0].message.content.strip()

def match_program(program: str, reason: str):
    """
    Filters mitigant data based on the GPT-predicted category.
    """
    prediction = categorize_reason_with_gpt(reason)
    predicted_categories = prediction.get("categories", [])
    if not predicted_categories:
        return {
            "matched_categories": [],
            "results": "No matching categories found for the given reject reason."
        }
    # print(reason)
    if(program.lower() == 'informal'):
       
        with open("prompts/Mitigation.txt", 'r', encoding='utf-8') as f:
            res = f.read()
            return res
        
    file_path = PROGRAM_FILES.get(program.lower())
    if not file_path:
        raise ValueError(f"Unknown program: {program}")

    with open(file_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    # print(records)
    # filtered = [
    #     {
    #         "Reject Category": r.get("Reject Category", ""),
    #         "Reject Reasons": r.get("Reject Reasons", ""),
    #         "List of Mitigants": r.get("List of Mitigants ", ""),
    #         "Quantitative Measures \nMitigates": r.get("Quantitative measures, \nMitigates", "")
    #     }
    #     for r in records
    #     if r.get("Reject Category", "").lower().strip() == predicted_category.lower()
    # ]
    results_by_category = {}
    for category in predicted_categories:
        print(f"Processing category: {category}")
        filtered = [
                {
                    "Reject Category Finalization": r.get("Reject Category", "").strip(),
                    "Reject Reasons": r.get("Reject Reasons", "").strip(),
                    "List of Mitigants": r.get("List of Mitigants ", "").strip(),
                    "Quantitative Measures": r.get("Quantitative measures, \nMitigates", "").strip()
                }
                for r in records
                if r.get("Reject Category", "").lower().strip() == category.lower()
        ]

        results_by_category[category] = filtered if filtered else "No matches found for this category"
    print(results_by_category)
    # print(filtered)
    if len(filtered) != 0 :
        filtered = filtered
    else:
        filtered = predicted_categories

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

1️⃣ Rule : Combine conteually Similar Reject Reasons Within Same category

Freely combine all mitigants and quantitive measure from **all related reasons within that category** even if they appear in different data objects.
Must combine all mitigants and quantitive measures from these matched reasons-even they are spread accross different input objects
Consider the reject reason matched if it **partially matched or share context** with existing one in the same category
Ensure the response includes **deduplicated** and **generalized** mitigants and quantitive measure from merged group.
Never include mitigants from a different reject category.


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
✔ Are combined mitigants  and quantitive measers only from the same reject category?
✔ Are all suggestions framed as guidance (e.g., "Provide," "Ensure")?
✔ Have all figures been translated into quantitative terms, including both mitigants and quantitative measures?
✔ Are mitigants and measure merged for same category?
✔ Have you avoided assuming outcome or cause?
✔ Are approval/program flags mentioned, if present in mitigants?
✔ Is the language neutral, non-committal, and future-oriented?
✔ Have you avoided personal, familial, or relational references?
✔ Have you provided quantitive and list of mitigants seperate ?

🔹 This ensures responses are:
Guidance-oriented

Neutral and non-prescriptive

Compliant and scalable for future rejection scenarios

Only refer to the below reject reasons and categories to provide mitigants and quantitative measures:

----------------------------------
{results_by_category}

-----------------------
At the end of the response, include this statement verbatim:

Listed measures for credit mitigants are exhaustive and limited to {program} cases, they may vary case to case basis. However, it is advisable to refer these mitigants before file login.
"""

# print(match_program("Prime" ,"low business vintage please suggest mitigants"))