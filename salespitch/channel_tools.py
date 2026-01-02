import os
import json
from langchain.tools import StructuredTool
from .eligibility_calcultor1 import home_loan_eligibility
from .step_up_calculator import step_up_calculator
from .step_down_joint import step_down
from .step_down_pension import step_down_pension
from .login_checklist import logincheck_documents

def home_loan_eligibility_tool(customer_type, dob, net_monthly_income, current_monthly_emi, roi):
    """Calculate the maximum home loan amount a customer is eligible for."""
    return home_loan_eligibility(customer_type, dob, net_monthly_income, current_monthly_emi, roi)

def step_up_calculator_tool(net_monthly_income, obligations, working_sector, total_tenure_months, rate, primary_tenure_months):
    """Calculate the step-up loan amount."""
    return step_up_calculator(net_monthly_income, obligations, working_sector, total_tenure_months, rate, primary_tenure_months)

def step_down_joint_income_calculator_tool(customer_type, salaried_son_dob, salaried_dad_dob, salaried_son_current_net_monthly_income, salaried_dad_current_net_monthly_income, salaried_dad_obligations, salaried_son_obligations, salaried_son_ROI, salaried_dad_ROI, salaried_dad_age, salaried_son_age):
    """Determine the total loan eligibility based on son's and dad's financial profiles."""
    return step_down(customer_type, salaried_son_dob, salaried_dad_dob, salaried_son_current_net_monthly_income, salaried_dad_current_net_monthly_income, salaried_dad_obligations, salaried_son_obligations, salaried_son_ROI, salaried_dad_ROI, salaried_dad_age, salaried_son_age)

def step_down_pension_income_calculator_tool(dob_of_person, monthly_income_from_salary, monthly_income_from_pension, salaried_obligations, pension_obligations, salaried_requested_tenure, pension_requested_tenure, pension_ROI, salaried_ROI, age_of_person, IMGC):
    """Calculate the pension income eligibility."""
    return step_down_pension(dob_of_person, monthly_income_from_salary, monthly_income_from_pension, salaried_obligations, pension_obligations, salaried_requested_tenure, pension_requested_tenure, pension_ROI, salaried_ROI, age_of_person, IMGC)

def logincheck_documents_tool(employment, eligibility_method=None, rental_income=False, other_income=False):
    """Get the list of required documents for login."""
    return logincheck_documents(employment.lower(), eligibility_method.lower(), rental_income, other_income)


def get_product_info(product_name):
    """Retrieve product information from a text file."""
    try:
        with open(f"channel_info/{product_name}.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Product information for '{product_name}' not found."

def get_product_descriptions():
    """Load product descriptions from a JSON file."""
    try:
        with open("prompts/product_descriptions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def create_product_info_tool(product_name, abhfl_instance):
    """Create a tool to retrieve information about a specific product."""
    tool_name = product_name.lower().replace(" ", "_") + "_info"
    product_descriptions = get_product_descriptions()
    
    if product_name in product_descriptions:
        tool_description = product_descriptions[product_name]
    else:
        tool_description = f"Retrieve detailed information about the {product_name} product."
    
    def product_info_tool():
        product_info = get_product_info(product_name)
        with open("prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
            text = f.read()
        # Append product info to system message
        abhfl_instance.append_to_system_message(text + product_info)
        return product_info

    return StructuredTool.from_function(
        func=product_info_tool,
        name=tool_name,
        description=tool_description,
    )

def create_tools(abhfl_instance):
    """Create and return a list of StructuredTools."""
    tools = [
        # Calculator Tools
        StructuredTool.from_function(
            func=home_loan_eligibility_tool,
            name="home_loan_eligibility_tool",
            description="""Calculate the maximum home loan amount a customer is eligible for based on their profile.
            Parameters:
            customer_type (str, required): Type of the customer (e.g., salaried, self-employed).
            dob (str, required): Date of birth of the customer in dd Month yyyy format.(arrange dob in 05 August 2025 format only)
            net_monthly_income (float, required): The customer's net monthly income.
            current_monthly_emi (float, required): The customer's current monthly financial obligations.
            roi (float, required): Rate of interest for the loan.""",
        ),
        StructuredTool.from_function(
            func=step_up_calculator_tool,
            name="step_up_calculator_tool",
            description="""Calculate the step-up loan amount based on various income and loan parameters.
            Parameters:
            net_monthly_income (float, required): The net monthly income of the applicant.
            obligations (float, required): Monthly financial obligations.
            working_sector (str, required): The sector in which the applicant is employed.
            total_tenure_months (int, required): The total loan tenure in months.
            rate (float, required): The applicable rate of interest on the loan.
            primary_tenure_months (int, required): The tenure for the primary loan phase.""",
        ),
        StructuredTool.from_function(
            func=step_down_joint_income_calculator_tool,
            name="step_down_joint_income_calculator_tool",
            description="""Determine the total loan eligibility based on the son's and dad's financial profiles.
            Parameters:
            customer_type (str, required): Type of customer.
            salaried_son_dob (str, required): Son's date of birth.
            salaried_dad_dob (str, required): Dad's date of birth.
            salaried_son_current_net_monthly_income (float, required): Son's net monthly income.
            salaried_dad_current_net_monthly_income (float, required): Dad's net monthly income.
            salaried_dad_obligations (float, required): Dad's monthly financial obligations.
            salaried_son_obligations (float, required): Son's monthly financial obligations.
            salaried_son_ROI (float, required): Son's applicable loan rate of interest.
            salaried_dad_ROI (float, required): Dad's applicable loan rate of interest.""",
        ),
        StructuredTool.from_function(
            func=step_down_pension_income_calculator_tool,
            name="step_down_pension_income_calculator_tool",
            description="""Calculate the pension income eligibility based on various financial parameters.
            Parameters:
            dob_of_person (str, required): Date of birth of the person.
            monthly_income_from_salary (float, required): Monthly income from salary.
            monthly_income_from_pension (float, required): Monthly income from pension.
            salaried_obligations (float, required): Monthly financial obligations from salary.
            pension_obligations (float, required): Monthly financial obligations from pension.
            salaried_requested_tenure (int, required): Requested tenure for salaried income.
            pension_requested_tenure (int, required): Requested tenure for pension income.
            pension_ROI (float, required): Applicable rate of interest for the pension loan.
            salaried_ROI (float, required): Applicable rate of interest for the salaried loan.""",
        ),
        StructuredTool.from_function(
            func=logincheck_documents_tool,
            name="logincheck_documents_tool",
            description="""Get the list of required documents for login based on customer type, eligibility method, and income considerations.
            Parameters:
            employment (str, required): The employment type (e.g., 'salaried', 'self employed').
            eligibility_method (str, required): The eligibility method based on the customer type.
            rental_income (bool, required): Whether rental income is considered.
            other_income (bool, required): Whether other income is considered.""",
        )
    ]
    
    # Product information tools
    product_names = [
        # "Collateral",
        "salary_income_method",
        "cash_profit_method",
        "gross_turnover_method",
        "average_banking_program",
        "gross_profit_method",
        "gross_receipt_method",
        "gst_program",
        "pure_rental_program",
        "mortgage_product",
        "low_LTV_method",
        "credit_manager_assessed_income_program",
        "pragati_home_loan",
        "pragati_plus",
        "pragati_aashiyana",
        "general_purpose_loan",
        "micro_LAP",
        "micro_CF",
        "step_up",
        "step_down",
        "extended_tenure",
        "lease_rental_discounting",
        "express_balance_transfer_program",
        "prime_hl",
        "prime_lap",
        "priority_balance_transfer",
        "semi_fixed",
        "power_pitches",
        "PMAY",
        "Khushi_home_loan",
        "Negative_and_caution_Profiles"
    ]
    
    # Add product information tools
    for product_name in product_names:
        tools.append(create_product_info_tool(product_name, abhfl_instance))
    #print(f"Total tools created Channel: {len(tools)}")
    return tools
