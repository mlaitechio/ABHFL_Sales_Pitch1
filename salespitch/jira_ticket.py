"""
JIRA Service Desk - Ticket Creation Script
Flow: Validate Account → Create Account (if needed) → Create Issue
Field mapping based on user-friendly input labels (lowercase with underscores).
"""

import os
import re

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

AUTH = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)

SESSION = requests.Session()
SESSION.auth = AUTH
SESSION.headers.update({"Accept": "application/json"})

# Proxy is mandatory on this server — direct connection to Atlassian is blocked
if os.getenv("USE_PROXY", "false").lower() == "true":
    SESSION.proxies = {
        "http":  "http://185.46.212.88:80",
        "https": "http://185.46.212.88:443",
    }
REQUEST_TIMEOUT = (10, 30)  # (connect_timeout, read_timeout) in seconds


# ─── Field Mappings (lowercase_underscore key → JIRA ID) ─────────────────────

ISSUE_CATEGORY_MAP = {                       # customfield_10177
    "bug":              "10566",
    "service_request":  "10567",
}

ZONE_MAP = {                                 # customfield_10143
    "north": "10402",
    "south": "10403",
    "east":  "10404",
    "west":  "10405",
}

MODULE_MAP = {                               # customfield_10527
    "sourcing":      "11103",
    "login":         "11104",
    "dde_&_dqc":     "11105",
    "fde_&_fqc":     "11106",
    "underwriting":  "11107",
    "disbursement":  "11108",
    "master":        "11426",
    "technical":     "11427",
    "rcu":           "11428",
    "dashboard":     "11429",
    "lms_push":      "11994",
}

CATEGORY_MAP = {                             # customfield_10528
    "verification":        "11109",
    "applicant_details":   "11110",
    "product_details":     "11111",
    "documents":           "11114",
    "approval":            "11124",
}

SUB_CATEGORY_MAP = {                         # customfield_10529
    "pan_verification":    "11133",
    "aadhar_verification": "11134",
    "applicant_details":   "11142",
    "login_issue":         "11402",
    "api_integration":     "11403",
    "other":               "11401",
}

SUB_SUB_CATEGORY_MAP = {                     # customfield_10530
    "self":                       "11153",
    "other_user":                 "11154",
    "personal_details":           "11155",
    "kyc_detail":                 "11156",
    "loan_details":               "11161",
    "submit_for_underwriting":    "11171",
    "other":                      "11400",
}

# All maps keyed by friendly field name (for generic lookup)
FIELD_MAPS = {
    "issue_category":    ISSUE_CATEGORY_MAP,
    "zone":              ZONE_MAP,
    "module":            MODULE_MAP,
    "category":          CATEGORY_MAP,
    "sub_category":      SUB_CATEGORY_MAP,
    "sub_sub_category":  SUB_SUB_CATEGORY_MAP,
}

# Reverse: pretty labels for the bot to show users
FIELD_OPTIONS = {
    field: list(mapping.keys()) for field, mapping in FIELD_MAPS.items()
}


def resolve_field(field_name: str, label: str) -> str:
    """Resolve a user label (lowercase_underscore) to its JIRA ID."""
    mapping = FIELD_MAPS.get(field_name)
    if mapping is None:
        raise ValueError(f"Unknown field: '{field_name}'")
    normalized = label.strip().lower().replace(" ", "_")
    if normalized in mapping:
        return mapping[normalized]
    valid = ", ".join(mapping.keys())
    raise ValueError(
        f"Invalid value '{label}' for '{field_name}'. Valid options: {valid}"
    )


# ─── 1. Validate Account ────────────────────────────────────────────────────
def validate_account(email: str) -> tuple[str, str] | tuple[None, None]:
    """
    Search for an existing JIRA user by email.
    Returns (accountId, displayName) if found, (None, None) otherwise.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/user/search"
    params = {"query": email}

    try:
        response = SESSION.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0].get("accountId"), users[0].get("displayName", "")
        return None, None
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Jira API error in validate_account: {e}")


# ─── 2. Create Customer ─────────────────────────────────────────────────────
def create_customer(display_name: str, email: str) -> str | None:
    """
    Create a new customer in JIRA Service Desk.
    Returns the accountId of the newly created customer.
    """
    url = f"{JIRA_BASE_URL}/rest/servicedeskapi/customer"
    payload = {
        "displayName": display_name,
        "email": email
    }

    try:
        response = SESSION.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code in (200, 201):
            return response.json().get("accountId")
        return None
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Jira API error in create_customer: {e}")


# ─── 3. Create Issue ─────────────────────────────────────────────────────────
def create_issue(
    account_id: str,
    summary: str,
    description: str,
    zone: str,
    module: str,
    category: str,
    sub_category: str,
    sub_sub_category: str,
    application_no: str = None,
) -> dict | None:
    """
    Raise a JIRA Service Desk request on behalf of the given accountId.
    Issue type is always Bug (hardcoded). application_no is optional.
    All dropdown fields accept lowercase_underscore labels (e.g. "north").
    """
    url = f"{JIRA_BASE_URL}/rest/servicedeskapi/request"

    payload = {
        "serviceDeskId": "8",
        "requestTypeId": "103",
        "requestFieldValues": {
            "summary":            summary,
            "description":        description,
            "customfield_10183":  application_no if application_no else "",
            "customfield_10177":  {"id": resolve_field("issue_category", "bug")},
            "customfield_10143":  {"id": resolve_field("zone", zone)},
            "customfield_10527":  {"id": resolve_field("module", module)},
            "customfield_10528":  {"id": resolve_field("category", category)},
            "customfield_10529":  {"id": resolve_field("sub_category", sub_category)},
            "customfield_10530":  {"id": resolve_field("sub_sub_category", sub_sub_category)},
        },
        "raiseOnBehalfOf": account_id,
    }

    try:
        response = SESSION.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code in (200, 201):
            return response.json()
        return {"error": response.status_code, "detail": response.text}
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Jira API error in create_issue: {e}")


# ─── Main Flow (called by the agent tool) ────────────────────────────────────
def raise_jira_ticket(
    email: str,
    summary: str,
    description: str,
    zone: str,
    module: str,
    category: str,
    sub_category: str,
    sub_sub_category: str,
    application_no: str = None,
    application_name: str = None,
) -> str:
    """
    Complete JIRA ticket creation flow:
      1. Validate if account exists by email → gets accountId + displayName from JIRA
      2. If not found → create customer (display_name derived from email)
      3. Use the accountId to raise a JIRA issue

    Issue type is always Bug (hardcoded).
    application_no is optional — included in description if provided.
    application_name is for informational context only — appended to description if provided.

    All dropdown fields use lowercase_underscore keys:
      zone           : north | south | east | west
      module         : sourcing | login | dde_&_dqc | fde_&_fqc | underwriting | disbursement | master | technical | rcu | dashboard | lms_push
      category       : verification | applicant_details | product_details | documents | approval
      sub_category   : pan_verification | aadhar_verification | applicant_details | login_issue | api_integration | other
      sub_sub_category: self | other_user | personal_details | kyc_detail | loan_details | submit_for_underwriting | other
    """
    print(module, category, sub_category, sub_sub_category, application_no, application_name, summary, description, email, zone)

    enriched_description = description
    if application_name:
        enriched_description += f"\n\nApplication: {application_name}"
    if application_no:
        enriched_description += f"\nApplication No: {application_no}"

    # Step 1 — Validate and get display name directly from JIRA
    account_id, display_name = validate_account(email)

    # Step 2 — Create if not found (derive display_name from email as fallback)
    if account_id is None:
        local = email.split("@", 1)[0]
        parts = re.split(r"[^A-Za-z]+", local)
        parts = [p for p in parts if p]
        display_name = " ".join(p.title() for p in parts)
        account_id = create_customer(display_name, email)
        if account_id is None:
            return "❌ Failed: Could not create or find a customer account for the given email."

    # Step 3 — Create issue
    result = create_issue(
        account_id=account_id,
        summary=summary + "-- Raised from FinWise",
        description=enriched_description,
        zone=zone,
        module=module,
        category=category,
        sub_category=sub_category,
        sub_sub_category=sub_sub_category,
        application_no=application_no,
    )

    if result and "error" not in result:
        issue_key = result.get("issueKey", "N/A")
        return f"✅ JIRA ticket created successfully!\nIssue Key: {issue_key}\n"
    elif result and "error" in result:
        return f"❌ Failed to create JIRA ticket. Status: {result['error']}\nDetail: {result['detail']}"
    else:
        return "❌ Unknown error while creating JIRA ticket."


# ─── Entry Point (Example) ──────────────────────────────────────────────────
# if __name__ == "__main__":
#     print(raise_jira_ticket(
#         email="Sangeeta.Mansabdar@adityabirlacapital.com",
#         summary="Test Login Issue",
#         description="User cannot login since morning.",
#         zone="north",
#         module="login",
#         category="verification",
#         sub_category="login_issue",
#         sub_sub_category="self",
#         application_no=None,
#         application_name="Finverse",
#     ))