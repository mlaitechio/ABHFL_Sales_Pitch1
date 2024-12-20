import os
import tiktoken
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
import asyncio
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor
from langchain_community.callbacks import get_openai_callback
import numpy_financial as npf
from .eligibility_calcultor1 import home_loan_eligibility
from .part_payment1 import part_payment
from .emi_cal2 import emi_calc
from .loan_eligibility1 import loan_eligibility
from .step_up_calculator import step_up_calculator
from .BTS_calculator2 import bts_calc
from .step_down_joint import step_down
from .step_down_pension import step_down_pension
from .login_checklist import logincheck_documents
import pandas as pd
from langchain.agents import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.agents import AgentExecutor, create_tool_calling_agent
import time

load_dotenv()


class ABHFL:
    is_function_calling = 0
    is_sales_pitch_active = False
    is_rag_function_active = False

    def __init__(self, message):
        self.API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        # self.client = AzureOpenAI(api_key=self.API_KEY, api_version="2023-07-01-preview",
        #                           azure_endpoint=self.RESOURCE_ENDPOINT)
        self.Completion_Model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.client = AzureChatOpenAI(
            api_key=self.API_KEY,
            api_version="2023-07-01-preview",
            azure_endpoint=self.RESOURCE_ENDPOINT,
            azure_deployment=self.Completion_Model,
        )
        self.folder_path = "Prompts"
        self.message = message
        self.AZURE_COGNITIVE_SEARCH_ENDPOINT = os.getenv(
            "AZURE_COGNITIVE_SEARCH_ENDPOINT"
        )
        self.AZURE_COGNITIVE_SEARCH_API_KEY = os.getenv(
            "AZURE_COGNITIVE_SEARCH_API_KEY"
        )
        self.AZURE_COGNITIVE_SEARCH_INDEX_NAME = os.getenv(
            "AZURE_COGNITIVE_SEARCH_INDEX_NAME"
        )
        self.ENCODING = "cl100k_base"
        self.search_client = SearchClient(
            endpoint=self.AZURE_COGNITIVE_SEARCH_ENDPOINT,
            index_name=self.AZURE_COGNITIVE_SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(self.AZURE_COGNITIVE_SEARCH_API_KEY),
        )

        self.user_input = ""
        self.store = {}

    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def reset_system_message(self):
        """Reset SystemMessage to the original main2.txt prompt."""
        if not ABHFL.is_sales_pitch_active:
            with open("prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
                text = f.read()
            # Clear previous system messages and set the original prompt
            self.message = [SystemMessage(content=f"{text}")]

    @staticmethod
    def home_loan_eligibility_tool(
        customer_type=None,
        dob=None,
        net_monthly_income=None,
        current_monthly_emi=None,
        roi=None,
    ):

        max_loan_amount = home_loan_eligibility(
            customer_type, dob, net_monthly_income, current_monthly_emi, roi
        )
        # print(max_loan_amount)
        return max_loan_amount

    @staticmethod
    def part_payment_tool(
        loan_outstanding=None,
        tenure_total_months=None,
        roi=None,
        part_payment_amount=None,
        current_emi=None,
    ):

        part_payment_cal = part_payment(
            loan_outstanding, tenure_total_months, roi, part_payment_amount, current_emi
        )

        return part_payment_cal

    @staticmethod
    def emi_calc_tool(
        principal=None, tenure_total_months=None, roi=None, emi=None, percentage=None
    ):

        emi = emi_calc(principal, tenure_total_months, roi, emi, percentage)

        return emi

    @staticmethod
    def loan_eligibility_tool(
        total_income=None,
        total_obligations=None,
        customer_profile=None,
        tenure_total_years=None,
        roi=None,
        foir=None,
    ):

        total_loan = loan_eligibility(
            total_income,
            total_obligations,
            customer_profile,
            tenure_total_years * 12,
            roi / 100,
            foir,
        )

        return total_loan

    @staticmethod
    def bts_calc_tool(
        sanction_amount=None,
        tenure_remaining_months=None,
        existing_roi=None,
        abhfl_roi=None,
        month_of_disbursement=None,
    ):
        """Calculate the benefit of transfer of sanction (BTS) value based on the loan parameters.(switching the loan)

        Parameters:
        sanction_amount (float, required): The sanctioned loan amount in integer.
        tenure_remaining (int, required): Remaining loan tenure in months (e.g., if the original tenure was 25 years, enter 300 months directly, not as 25 * 12).
        existing_roi (float, required): The current rate of interest on the loan.
        abhfl_roi (float, required): The proposed rate of interest after transfer.
        month_of_disbursement (str, required): The month of loan disbursement in %b-%y format (e.g., 'Aug-23').
        """

        BTS_value = bts_calc(
            sanction_amount,
            tenure_remaining_months,
            existing_roi,
            abhfl_roi,
            month_of_disbursement,
        )

        return BTS_value

    @staticmethod
    def step_up_calculator_tool(
        net_monthly_income=None,
        obligations=None,
        working_sector=None,
        total_tenure_months=None,
        rate=None,
        primary_tenure_months=None,
    ):

        emi = step_up_calculator(
            net_monthly_income,
            obligations,
            working_sector,
            total_tenure_months,
            rate,
            primary_tenure_months,
        )

        return emi

    @staticmethod
    def step_down_joint_income_calculator_tool(
        customer_type=None,
        salaried_son_dob=None,
        salaried_dad_dob=None,
        salaried_son_current_net_monthly_income=None,
        salaried_dad_current_net_monthly_income=None,
        salaried_dad_obligations=None,
        salaried_son_obligations=None,
        salaried_son_ROI=None,
        salaried_dad_ROI=None,
        salaried_dad_age=None,
        salaried_son_age=None,
    ):
        result = step_down(
            customer_type,
            salaried_son_dob,
            salaried_dad_dob,
            salaried_son_current_net_monthly_income,
            salaried_dad_current_net_monthly_income,
            salaried_dad_obligations,
            salaried_son_obligations,
            salaried_son_ROI,
            salaried_dad_ROI,
            salaried_dad_age,
            salaried_son_age,
        )
        return result

    @staticmethod
    def step_down_pension_income_calculator_tool(
        dob_of_person=None,
        monthly_income_from_salary=None,
        monthly_income_from_pension=None,
        salaried_obligations=None,
        pension_obligations=None,
        salaried_requested_tenure=None,
        pension_requested_tenure=None,
        pension_ROI=None,
        salaried_ROI=None,
        age_of_person=None,
        IMGC=None,
    ):
        result = step_down_pension(
            dob_of_person,
            monthly_income_from_salary,
            monthly_income_from_pension,
            salaried_obligations,
            pension_obligations,
            salaried_requested_tenure,
            pension_requested_tenure,
            pension_ROI,
            salaried_ROI,
            age_of_person,
            IMGC,
        )
        return result
    
    @staticmethod
    def logincheck_documents_tool(employment, eligibility_method=None, rental_income=False, other_income=False):

        result = logincheck_documents(employment.lower(), eligibility_method.lower(), rental_income, other_income)

        return result

    def generate_method(self, prompt_name):
        """Generic method to handle various prompts and update system message."""
        prompt_path = f"prompts/{prompt_name}.txt"
        question = self.user_input
        with open(prompt_path, "r", encoding="utf-8") as f:
            text = f.read()
        with open("prompts/main_prompt1.txt", "r", encoding="utf-8") as f:
            main = f.read()
        # Replace existing SystemMessage if present
        replaced = False
        for i, message in enumerate(self.message):
            if isinstance(message, SystemMessage):
                self.message[i] = SystemMessage(
                    content=f"""{main  + text}
Must Provide Concice Answer: """
                )
                replaced = True
                break

        if not replaced:
            self.message.append(SystemMessage(content=f"{main}"))

        # Append the question as a HumanMessage
        # self.message.append(HumanMessage(content=question))

        return text

    def collateral_type(self):
        return self.generate_method("Collateral")

    def salary_income_method(self):
        return self.generate_method("salary_income_method")

    def cash_profit_method(self):
        return self.generate_method("cash_profit_method")

    def gross_turnover_method(self):
        return self.generate_method("gross_turnover_method")

    def average_banking_program(self):
        return self.generate_method("average_banking_program")

    def gross_profit_method(self):
        return self.generate_method("gross_profit_method")

    def gross_receipt_method(self):
        return self.generate_method("gross_receipt_method")

    def gst_program(self):
        return self.generate_method("gst_program")

    def pure_rental_program(self):
        return self.generate_method("pure_rental_program")

    def mortgage_product(self):
        return self.generate_method("mortgage_product")

    def low_LTV_method(self):
        return self.generate_method("low_LTV_method")

    def credit_manager_assessed_income_program(self):
        return self.generate_method("credit_manager_assessed_income_program")

    def ABHFL_branch_categorization(self):
        return self.generate_method("ABHFL_branch_categorization")

    def pragati_home_loan(self):
        return self.generate_method("pragati_home_loan")

    def pragati_plus(self):
        return self.generate_method("pragati_plus")

    def pragati_aashiyana(self):
        return self.generate_method("pragati_aashiyana")

    def pragati_aashiyana_segment_1(self):
        return self.generate_method("pragati_aashiyana_segment_1")

    def pragati_aashiyana_segment_2(self):
        return self.generate_method("pragati_aashiyana_segment_2")

    def general_purpose_loan(self):
        return self.generate_method("general_purpose_loan")

    def micro_LAP(self):
        return self.generate_method("micro_LAP")

    def micro_CF(self):
        return self.generate_method("micro_CF")

    def step_up(self):
        return self.generate_method("step_up")

    def step_down(self):
        return self.generate_method("step_down")

    def extended_tenure(self):
        return self.generate_method("extended_tenure")

    def lease_rental_discounting(self):
        return self.generate_method("lease_rental_discounting")

    def express_balance_transfer_program(self):
        return self.generate_method("express_balance_transfer_program")

    def prime_home_loan(self):
        return self.generate_method("prime_hl")

    def prime_lap(self):
        return self.generate_method("prime_lap")

    def priority_balance_transfer(self):
        return self.generate_method("priority_balance_transfer")

    def semi_fixed(self):
        return self.generate_method("semi_fixed")

    def staff_loan_price(self):
        return self.generate_method("staff_loan_price")

    def power_pitch(self):
        return self.generate_method("power_pitches")
    
    def nri_assesment(self):
        return self.generate_method("nri_assesment_criteria")
    
    def pmay(self):
        return self.generate_method("PMAY")

    def all_other_information(self, *args, **kwargs):
        """Function provides all details for products such as 'Express Balance Transfer Program,' 'BT+Top Up – Illustration,' 'Priority Balance Transfer,' 'Extended Tenure,' 'Step-Down,' 'Step-Up,' 'Lease Rental Discounting,' 'Micro CF,' 'Micro LAP,' 'General Purpose Loan,' 'Pragati Aashiyana (Segment 2),' 'Pragati Aashiyana (Segment 1),' 'Pragati Aashiyana,' 'Pragati Plus,' 'Pragati Home Loan,' 'ABHFL Branch Categorization,' 'Credit Manager Assessed Income Program,' 'GST Program,' 'Pure Rental Program,' 'Low LTV Method,' 'Average Banking Program (ABP),' 'Gross Profit Method,' 'Gross Receipt Method,' 'Gross Turnover Method,' 'Cash Profit Method (CPM),' 'Salary Income Method,' 'Key Product Solutions,' and 'Mortgage Product."""
        if not ABHFL.is_rag_function_active:
            ABHFL.is_rag_function_active = True  # Set the flag to active

            print("Rag function called ")
            question = self.user_input
            # question = self.user_input
            max_tokens = 6000
            token_threshold = 0.8 * max_tokens  # 90% of max_tokens as threshold
            # print(token_threshold)
            # query_embedding = self.get_query_embedding(question)
            results = self.search_client.search(
                search_text=question,
                select=["product", "description"],
                # Include 'token' in the select query
                #    query_type=QueryType.SEMANTIC,
                #    semantic_configuration_name='my-semantic-config',
                #    query_caption=QueryCaptionType.EXTRACTIVE,
                #    query_answer=QueryAnswerType.EXTRACTIVE,
                top=3,
            )

            context = ""
            total_tokens = 0
            num_results = 0

            for result in results:
                # print("Result: " , result)
                title = result["product"]
                content = result["description"]
                result_tokens = self.num_tokens_from_string(context, self.ENCODING)
                # print(result_tokens)
                # Check if adding this result exceeds the token limit
                if total_tokens + result_tokens > token_threshold:
                    excess_tokens = total_tokens + result_tokens - token_threshold
                    # Reduce the length of the context by truncating it
                    context = context[: -int(excess_tokens)]
                    break

                # Add this result to context
                # print(title)
                context += f"{{'Title': {title} , 'Product Details': {content} }}\n "
                total_tokens += result_tokens
                num_results += 1

            if ABHFL.is_function_calling != 12:
                # with open("prompts/rag_prompt.txt", 'r') as file:
                with open("prompts/main_prompt1.txt", "r") as file:
                    header = file.read()
                header = f"""{header}
                    Context : {context}
                    Question : {question}
                    Consice and accurate answer :
                    """
                # print(question)
                # Replace existing SystemMessage if present
                replaced = False
                for i, message in enumerate(self.message):
                    if isinstance(message, SystemMessage):
                        self.message[i] = SystemMessage(content=f"{header}")
                        replaced = True
                        break
                print(self.message)
                if not replaced:
                    self.message.append(SystemMessage(content=f"{header}"))

                # self.message.append(HumanMessage(content=self.user_input))
                ABHFL.is_function_calling = 12
        # Replace the placeholder "{question}" in the header with the actual question

    def generate_salespitch(self, *args, **kwargs):
        """Generate a sales pitch."""
        if not ABHFL.is_sales_pitch_active:
            ABHFL.is_sales_pitch_active = True  # Set the flag to active
            print("Sales pitch function called")
            with open("prompts/sales_pitch1.txt", "r", encoding="utf-8") as f:
                text = f.read()

            # Replace existing SystemMessage if present
            replaced = False
            for i, message in enumerate(self.message):
                if isinstance(message, SystemMessage):
                    self.message[i] = SystemMessage(content=f"{text}")
                    replaced = True
                    break

            if not replaced:
                self.message.append(SystemMessage(content=f"{text}"))

            self.message.append(HumanMessage(content=self.user_input))
            ABHFL.is_function_calling = 11

    async def run_conversation(self, user_input):
        self.user_input = user_input
        self.message.append(HumanMessage(content=user_input))
        # Initialize the tools
        tools = [
            StructuredTool.from_function(
                func=self.home_loan_eligibility_tool,
                description="""Calculate the maximum home loan amount a customer is eligible for based on their profile.

        Parameters:
        customer_type (str, required): Type of the customer (e.g., salaried, self-employed).
        dob (str, required): Date of birth of the customer in dd Month yyyy format.
        net_monthly_income (float, required): The customer's net monthly income.
        current_monthly_emi (float, required): The customer's current monthly financial obligations.
        roi (float, required): Rate of interest for the loan.""",
            ),
            StructuredTool.from_function(
                func=self.part_payment_tool,
                description=""" Calculate the impact of part payment on the loan, including the reduction in tenure or EMI.

        Parameters:
        loan_outstanding (float,required): The current outstanding loan amount.
        tenure_months (int,required): Remaining tenure of the loan in months.
        roi (float,required): Rate of interest for the loan.
        part_payment_amount (float,required): The amount of part payment being made.
        current_emi (float,required): The current EMI amount.
.""",
            ),
            StructuredTool.from_function(
                func=self.emi_calc_tool,
                description="""Calculate the EMI, interest,principal, or tenure of a loan based on the provided inputs.

        Parameters:
        principal (float,required): The principal loan amount.
        tenure_months (int,required): The loan tenure in months.
        roi (float,required): Rate of interest for the loan.
        emi (float,required): The equated monthly installment amount.
        percentage (float,required): Percentage adjustment for calculating EMI.
""",
            ),
            #             StructuredTool.from_function(
            #                 func=self.loan_eligibility_tool,
            #                 description="""        Determine the total loan amount a customer is eligible for based on their financial profile.
            #         Parameters:
            #         total_income (float): The customer's total monthly income.
            #         total_obligations (float): The customer's total monthly obligations.
            #         customer_profile (str): The customer's profile (e.g., salaried, self-employed).
            #         tenure_months (int): The loan tenure in months.
            #         roi (float): Rate of interest for the loan.
            # """
            #             ),
            StructuredTool.from_function(
                func=self.bts_calc_tool,
                description="""Calculate the benefit of transfer of sanction (BTS) value based on the loan parameters.(switching the loan)
    Parameters:
        sanction_amount (float,required): The sanctioned loan amount in integer.
         tenure_remaining_months (int,required): Remaining loan tenure in months (e.g., if the original tenure was 25 years, enter 300 months directly, not as 25 * 12).
        existing_roi (float,required): The current rate of interest on the loan.
        abhfl_roi (float,required): The proposed rate of interest after transfer.
        month_of_disbursement[month-year] (str , required): The month of loan disbursement in %b-%y format (e.g., 'Aug-23').
        """,
            ),
            StructuredTool.from_function(
                func=self.step_up_calculator_tool,
                description="""Calculate the step-up loan amount based on various income and loan parameters.
            Note:  Minimum Net monthly income must be 40k,
                   The primary tenure must be an between 36 and 60 months only.
            Parameters:
            net_monthly_income (float, required): The net monthly income of the applicant.
            obligations (float, required): Monthly financial obligations (e.g., EMI, debts).
            working_sector (str, required): The sector in which the applicant is employed from 'Industrial' 'Service' 'Manufacturing'.
            total_tenure (int, required): The total loan tenure in months (e.g., 240 months).
            rate (float, required): The applicable rate of interest on the loan.
            primary_tenure (int, required): The tenure for the primary loan phase.
            """,
            ),
            StructuredTool.from_function(
                func=self.step_down_joint_income_calculator_tool,
                description="""Determine the total loan eligibility for the customer based on the son's and dad's financial profiles. If no input values are provided, return None.
        Note:  Both must be salaried. self-employed not eligible for step-down
Parameters:
- customer_type (str, required): Type of customer (e.g., salaried, self-employed).
- salaried_son_dob (str, required): Son's date of birth (e.g., "15 November 1994").
- salaried_dad_dob (str, required): Dad's date of birth (e.g., "15 November 1994").
- salaried_son_current_net_monthly_income (float, required): Son's net monthly income.
- salaried_dad_current_net_monthly_income (float, required): Dad's net monthly income.
- salaried_dad_obligations (float, required): Dad's monthly financial obligations (e.g., EMI, debts).
- salaried_son_obligations (float, required): Son's monthly financial obligations (e.g., EMI, debts).
- salaried_son_ROI (float, required): Son's applicable loan rate of interest.
- salaried_dad_ROI (float, required): Dad's applicable loan rate of interest.
        """,
            ),
            StructuredTool.from_function(
                func=self.step_down_pension_income_calculator_tool,
                description="""Calculate the pension income eligibility based on various financial parameters of the individual.
    Parameters:
    - dob_of_person (str, required): Date of birth of the person (e.g., "15 November 1994").
    - monthly_income_from_salary (float, required): Monthly income from salary.
    - monthly_income_from_pension (float, required): Monthly income from pension.
    - salaried_obligations (float, required): Monthly financial obligations from salary (e.g., EMI, debts).
    - pension_obligations (float, required): Monthly financial obligations from pension (e.g., EMI, debts).
    - salaried_requested_tenure (int, required): Requested tenure for salaried income.
    - pension_requested_tenure (int, required): Requested tenure for pension income.
    - pension_ROI (float, required): Applicable rate of interest for the pension loan.
    - salaried_ROI (float, required): Applicable rate of interest for the salaried loan.
    - age_of_person (int, required): Age of the person.
    """,
            ),
            # StructuredTool.from_function(
            #     func=self.generate_salespitch,
            #     description="Function provide a personalized recommendation and solution for an ABHFL home loan based on the customer information"
            # ),
            # StructuredTool.from_function(
            #     func=self.all_other_information,
            #     description="Function provides all details for products such as 'Express Balance Transfer Program,' 'BT+Top Up – Illustration,' 'Priority Balance Transfer,' 'Extended Tenure,' 'Step-Down,' 'Step-Up,' 'Lease Rental Discounting,' 'Micro CF,' 'Micro LAP,' 'General Purpose Loan,' 'Pragati Aashiyana (Segment 2),' 'Pragati Aashiyana (Segment 1),' 'Pragati Aashiyana,' 'Pragati Plus,' 'Pragati Home Loan,' 'ABHFL Branch Categorization,' 'Credit Manager Assessed Income Program,' 'GST Program,' 'Pure Rental Program,' 'Low LTV Method,' 'Average Banking Program (ABP),' 'Gross Profit Method,' 'Gross Receipt Method,' 'Gross Turnover Method,' 'Cash Profit Method (CPM),' 'Salary Income Method,' 'Key Product Solutions,' and 'Mortgage Product.'"
            # ),
            StructuredTool.from_function(
                func=self.salary_income_method,
                description="Function Delivers detailed information about the salary income method for financial evaluation.",
            ),
            StructuredTool.from_function(
                func=self.cash_profit_method,
                description="Function Provides in-depth information related to the cash profit method used for assessing financials.",
            ),
            StructuredTool.from_function(
                func=self.gross_turnover_method,
                description="Function Retrieves complete information on the gross turnover method for evaluating financial eligibility.",
            ),
            StructuredTool.from_function(
                func=self.average_banking_program,
                description="Function Supplies all necessary details about the Average Banking Program (ABB).",
            ),
            StructuredTool.from_function(
                func=self.gross_profit_method,
                description="Function Offers information on the gross profit method for financial assessment.",
            ),
            StructuredTool.from_function(
                func=self.gross_receipt_method,
                description="Function Retrieves information regarding the gross receipt method.",
            ),
            StructuredTool.from_function(
                func=self.gst_program,
                description="Function Provides complete details about the GST program for evaluating financials.",
            ),
            StructuredTool.from_function(
                func=self.pure_rental_program,
                description="Function Offers detailed information on the pure rental program.",
            ),
            StructuredTool.from_function(
                func=self.mortgage_product,
                description="Function Provides all relevant information about mortgage products available.",
            ),
            StructuredTool.from_function(
                func=self.low_LTV_method,
                description="Function Delivers information on the Low Loan-to-Value (LTV) method used in financial evaluations.",
            ),
            StructuredTool.from_function(
                func=self.credit_manager_assessed_income_program,
                description="Function Provides details on the income assessment program conducted by credit managers.",
            ),
            StructuredTool.from_function(
                func=self.ABHFL_branch_categorization,
                description="Function Offers all information about ABHFL branch categorization.",
            ),
            StructuredTool.from_function(
                func=self.pragati_home_loan,
                description="Function Provides comprehensive details about the Pragati Home Loan product.Best Loan for Low Income Group",
            ),
            StructuredTool.from_function(
                func=self.pragati_plus,
                description="Function Offers information on the Pragati Plus loan program.",
            ),
            StructuredTool.from_function(
                func=self.pragati_aashiyana,
                description="Function Supplies detailed information about the Pragati Aashiyana program.Home Loan for Informal Sector Worker",
            ),
            StructuredTool.from_function(
                func=self.general_purpose_loan,
                description="Provides complete details on the general purpose loan offering.",
            ),
            StructuredTool.from_function(
                func=self.micro_LAP,
                description="Information about the Micro Loan Against Property (Micro LAP) program.Ideal loan for Small Business",
            ),
            StructuredTool.from_function(
                func=self.micro_CF,
                description="Offers details on the Micro CF (Commercial Finance) program.",
            ),
            StructuredTool.from_function(
                func=self.step_up,
                description="Provides information on the step-up program for home loans.",
            ),
            StructuredTool.from_function(
                func=self.step_down,
                description="Retrieves all relevant details on the step-down loan program.",
            ),
            StructuredTool.from_function(
                func=self.extended_tenure,
                description="Offers information on extended loan tenure options.",
            ),
            StructuredTool.from_function(
                func=self.priority_balance_transfer,
                description="Provides detailed information on the priority balance transfer program.(Priority BT)",
                return_direct=False,
            ),
            StructuredTool.from_function(
                func=self.lease_rental_discounting,
                description="Delivers complete information on the Lease Rental Discounting (LRD) program.",
            ),
            StructuredTool.from_function(
                func=self.express_balance_transfer_program,
                description="Offers details on the express balance transfer (express BT) program.",
            ),
            # StructuredTool.from_function(
            #     func = self.bt_top_up_illustration,
            #     description="Provides a detailed illustration of the BT+Top Up offering."
            # ),
            StructuredTool.from_function(
                func=self.prime_home_loan,
                description="Provides a detailed Prime Home Loan Details.",
            ),
            StructuredTool.from_function(
                func=self.prime_lap,
                description="Provides a detailed Prime Loan Against Property(LAP) ",
            ),
            StructuredTool.from_function(
                func=self.semi_fixed,
                description="Provides a detailed Semi fixed rates of all products",
            ),
            StructuredTool.from_function(
                func=self.staff_loan_price,
                description="Provides a detailed Pricing of staff Loan",
            ),
            StructuredTool.from_function(
                func=self.power_pitch,
                description="Provides a details of power pitch for abhfl products",
            ),
            StructuredTool.from_function(
                func=self.collateral_type,
                description="""
                Detailed all Properties and it's all Collateral type for PAN india in ABHFL
               
                """,
            ),
            StructuredTool.from_function(
                func=self.pmay,
                description="""
               Provides a Details about Pradhan Mantri Awas Yojana - Urban 2.0(PMAY)
                """,
            ),
            StructuredTool.from_function(
                func=self.nri_assesment,
                description="""
               Provides a Details about NRI salaried customers assesment criteria
                """,
            ),
            StructuredTool.from_function(
                func=self.logincheck_documents_tool,
                description="""Function to get the list of required documents for login based on customer type, eligibility method, and income considerations.
Parameters:
- customer_type (str, required): The type of customer (e.g., 'salaried', 'self employed').
- eligibility_method (str, required): The eligibility method based on the customer type.
    - If 'salaried', possible methods are: 'Cash Salaried', 'Bank Salaried', 'NRI Bank Salaried'.
    - If 'self-employed', possible methods are: 'Cash Profit Method', 'Gross Turnover', 'Gross Receipt', 
    'Gross Profit', 'ABB', 'GST', 'Low LTV', 'Pure Rental', 'Lease Rental Discounting', 
    'Express BT', 'Micro CF/Builder LAP', 'CM AIP'.
- rental_income (bool, required): Whether rental income is considered in eligibility (True/False).
    - Note:  Mark Yes in case of Pure Rental and LRD
- other_income (bool, required): Whether other income is considered in eligibility (True/False).
    - Note: Other income is only considered when the customer type is 'salaried'.
"""
                
            )
        ]

        # llm_with_tools = self.client.bind_tools(tools)
        # Check if we need to reset the SystemMessage
        if ABHFL.is_sales_pitch_active and ABHFL.is_function_calling == 11:
            ABHFL.is_sales_pitch_active = False  # Reset the flag
            self.reset_system_message()
        if ABHFL.is_rag_function_active and ABHFL.is_function_calling == 12:
            ABHFL.is_sales_pitch_active = False  # Reset the flag
            self.reset_system_message()

        MEMORY_KEY = "chat_history"
        prompt = ChatPromptTemplate.from_messages(
            [
                # ("system", """You are a key figure at Aditya Birla Housing Finance Limited (ABHFL), but you have only limited information about the company. """),
                (
                    "system",
                    """You are an expert conversational sales manager with access to various tools to deliver clear and concise answers. Select the most relevant tool for a precise response, avoiding unnecessary details. When responding to general or open-ended questions, always leverage tools for accuracy. If unsure of an answer, ask follow-up questions to clarify. You are experienced and professional in this role.""",
                ),
                MessagesPlaceholder(variable_name=MEMORY_KEY),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # agent = (
        #         {
        #             "input": lambda x: x["input"],
        #             "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
        #             "chat_history": lambda x: x["chat_history"],
        #         }
        #         | prompt
        #         | llm_with_tools
        #         | OpenAIToolsAgentOutputParser()
        # )
        agent = create_tool_calling_agent(self.client, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        max_response_tokens = 250
        token_limit = 50000

        # Helper function to calculate total tokens in the messages
        def calculate_token_length(messages):
            tokens_per_message = 3
            tokens_per_name = 1
            # encoding = tiktoken.get_encoding(self.ENCODING)
            encoding = tiktoken.encoding_for_model("gpt-4-0613")
            num_tokens = 0
            # print(len(messages))
            for message in messages:
                # print(message.content)
                num_tokens += tokens_per_message
                # for value in message.content:
                #     print(value)
                num_tokens += len(encoding.encode(message.content))
                # if key == "name":
                #     num_tokens += tokens_per_name
            num_tokens += 3
            # print(num_tokens)  # every reply is primed with <|start|>assistant<|message|>
            return num_tokens

        # Helper function to ensure message length is within limits
        def ensure_message_length_within_limit(message):
            # print("Lenth Function Called",messages[0])
            messages = self.message
            conv_history_tokens = calculate_token_length(self.message)

            while conv_history_tokens + max_response_tokens >= token_limit:
                # print("Conv History", conv_history_tokens)
                if len(self.message) > 1:
                    del self.message[1]  # Remove the oldest message
                    conv_history_tokens = calculate_token_length(self.message)

        with get_openai_callback() as cb:
            try:

                ensure_message_length_within_limit(
                    self.message
                )  # Reserve some tokens for functions and overhead
                async for chunk in agent_executor.astream_events(
                    {"input": user_input, "chat_history": self.message}, version="v1"
                ):
                    time.sleep(0.05)
                    yield chunk
                # response = agent_executor.invoke({"input": user_input, "chat_history": self.message})

                # return response["output"]

            except Exception as e:
                error_message = f"An error occurred: {e}"
                print(error_message)
                yield error_message
            # print("Token : ", cb)
