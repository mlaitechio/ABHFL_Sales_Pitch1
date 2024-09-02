import os
import tiktoken
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType
from langchain_core.messages import HumanMessage , SystemMessage
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
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
# from .BTS_calculator import bts_calc
from .BTS_calculator2 import bts_calc
load_dotenv()

class ABHFL:
    is_function_calling = 0
    is_sales_pitch_active = False
    def __init__(self,message):
        self.API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        # self.client = AzureOpenAI(api_key=self.API_KEY, api_version="2023-07-01-preview",
        #                           azure_endpoint=self.RESOURCE_ENDPOINT)
        self.Completion_Model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.client = AzureChatOpenAI(api_key=self.API_KEY, api_version="2023-07-01-preview", azure_endpoint=self.RESOURCE_ENDPOINT, azure_deployment=self.Completion_Model)
        self.folder_path = 'Prompts'
        self.message = message
        self.AZURE_COGNITIVE_SEARCH_ENDPOINT = os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT")
        self.AZURE_COGNITIVE_SEARCH_API_KEY = os.getenv("AZURE_COGNITIVE_SEARCH_API_KEY")
        self.AZURE_COGNITIVE_SEARCH_INDEX_NAME = os.getenv("AZURE_COGNITIVE_SEARCH_INDEX_NAME")
        print(self.AZURE_COGNITIVE_SEARCH_INDEX_NAME)
        self.ENCODING = "cl100k_base"
        self.search_client = SearchClient(endpoint=self.AZURE_COGNITIVE_SEARCH_ENDPOINT,
                                          index_name=self.AZURE_COGNITIVE_SEARCH_INDEX_NAME,
                                          credential=AzureKeyCredential(self.AZURE_COGNITIVE_SEARCH_API_KEY))
        
      
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
            # self.message = [SystemMessage(content=f"{text}")]
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

    # @staticmethod
    # def home_loan_eligibility_tool(customer_type=None, dob=None, net_monthly_income=None, current_monthly_emi=None, roi=None, down_payment=None):

    #     max_loan_amount = home_loan_eligibility(customer_type, dob, net_monthly_income, current_monthly_emi, roi , down_payment)
   
    #     return max_loan_amount
    
    @staticmethod
    def part_payment_tool(loan_outstanding=None, tenure_total_years=None, roi=None, part_payment_amount=None, current_emi=None):

        part_payment_cal = part_payment(loan_outstanding, tenure_total_years * 12, roi, part_payment_amount, current_emi)

        return part_payment_cal
    
    @staticmethod
    def emi_calc_tool(principal=None, tenure_total_years=None, roi=None, emi=None, percentage=None):

        emi = emi_calc(principal, tenure_total_years * 12, roi, emi, percentage)

        return emi
    
    @staticmethod
    def loan_eligibility_tool(total_income=None, total_obligations=None, customer_profile=None, tenure_total_years=None, roi=None, foir=None):
        
        total_loan = loan_eligibility(total_income, total_obligations,
         customer_profile, tenure_total_years * 12, roi/100, foir)
            
        return total_loan


    @staticmethod
    def bts_calc_tool(sanction_amount=None, remaining_tenure_in_years=None, existing_roi=None, abhfl_roi=None,
                      month_of_disbursement=None):
        """Calculate the benefit of transfer of sanction (BTS) value based on the loan parameters.(switching the loan)

        Parameters:
        sanction_amount (float, optional): The sanctioned loan amount in integer.
        tenure_remaining (int, optional): Remaining loan tenure in months (e.g., if the original tenure was 25 years, enter 300 months directly, not as 25 * 12).
        existing_roi (float, optional): The current rate of interest on the loan.
        abhfl_roi (float, optional): The proposed rate of interest after transfer.
        month_of_disbursement (str, optional): The month of loan disbursement in %b-%y format (e.g., 'Aug-23').
        """
        
        BTS_value = bts_calc(sanction_amount, remaining_tenure_in_years * 12, existing_roi, abhfl_roi , month_of_disbursement)

        return BTS_value

    def all_ABHFL_product_loan_information(self,*args, **kwargs):
        """Provide comprehensive information on all product offered by Aditya birla housing finance limited"""
        print("Rag function called ")
        question = self.user_input
        # question = self.user_input
        max_tokens = 6000
        token_threshold = 0.8 * max_tokens  # 90% of max_tokens as threshold
        print(token_threshold)
        results = self.search_client.search(search_text=question, select=["text"],
                                        # Include 'token' in the select query
                                        #    query_type=QueryType.SEMANTIC,
                                        #    semantic_configuration_name='my-semantic-config',
                                        #    query_caption=QueryCaptionType.EXTRACTIVE,
                                        #    query_answer=QueryAnswerType.EXTRACTIVE, 
                                           top=4)

        context = ""
        total_tokens = 0
        num_results = 0
        
        for result in results:
            print("Result: " , result)
            title = result['text']
            # content = result['content']
            result_tokens = self.num_tokens_from_string(context, self.ENCODING)
            print(result_tokens)
            # Check if adding this result exceeds the token limit
            if total_tokens + result_tokens > token_threshold:
                excess_tokens = total_tokens + result_tokens - token_threshold
                # Reduce the length of the context by truncating it
                context = context[:-int(excess_tokens)]
                break

            # Add this result to context
            print(title)
            context += f"Title: {title}\n "
            total_tokens += result_tokens
            num_results += 1

        if ABHFL.is_function_calling != 12:
            # with open("prompts/rag_prompt.txt", 'r') as file:
            with open("prompts/main_prompt2.txt", 'r') as file:
                header = file.read()
                ABHFL.is_function_calling = 12

        # Replace the placeholder "{question}" in the header with the actual question
            header = f'''{header}
            Context : {context}
            Question : {question}
            Consice and accurate answer :
             '''
            # print(header)
            self.message.clear()
            self.message.append(SystemMessage(content=f"{header}"))

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


    def run_conversation(self, user_input):
        self.user_input = user_input
        self.message.append(HumanMessage(content=user_input))
        # print("Previous conversation: ",self.message)
            # Initialize the tools
        tools = [
        #     StructuredTool.from_function(
        #         func=self.home_loan_eligibility_tool,
        #         description="""Calculate the maximum home loan amount a customer is eligible for based on their profile.

        # Parameters:
        # customer_type (str): Type of the customer (e.g., salaried, self-employed).
        # dob (str): Date of birth of the customer in %d %B %Y format.
        # net_monthly_income (float): The customer's net monthly income.
        # current_monthly_obligation (float): The customer's current monthly financial obligations.
        # down_payment (float): The down payment amount the customer is willing to make.
        # roi (float): Rate of interest for the loan."""
        #     ),
            StructuredTool.from_function(
                func=self.part_payment_tool,
                description=""" Calculate the impact of part payment on the loan, including the reduction in tenure or EMI.

        Parameters:
        loan_outstanding (float): The current outstanding loan amount.
        tenure_months (int): Remaining tenure of the loan in months.
        roi (float): Rate of interest for the loan.
        part_payment_amount (float): The amount of part payment being made.
        current_emi (float): The current EMI amount.
."""
            ),
            StructuredTool.from_function(
                func=self.emi_calc_tool,
                description="""Calculate the EMI, interest,principal, or tenure of a loan based on the provided inputs.

        Parameters:
        principal (float, optional): The principal loan amount.
        tenure_months (int, optional): The loan tenure in months.
        roi (float, optional): Rate of interest for the loan.
        emi (float, optional): The equated monthly installment amount.
        percentage (float, optional): Percentage adjustment for calculating EMI.
"""
            ),
            StructuredTool.from_function(
                func=self.loan_eligibility_tool,
                description="""        Determine the total loan amount a customer is eligible for based on their financial profile.

        Parameters:
        total_income (float): The customer's total monthly income.
        total_obligations (float): The customer's total monthly obligations.
        customer_profile (str): The customer's profile (e.g., salaried, self-employed).
        tenure_months (int): The loan tenure in months.
        roi (float): Rate of interest for the loan.
        foir (float): Fixed Obligation to Income Ratio.
"""
            ),
            StructuredTool.from_function(
                func=self.bts_calc_tool,
                description="""Calculate the benefit of transfer of sanction (BTS) value based on the loan parameters.(switching the loan)

        Parameters:
        sanction_amount (float, optional): The sanctioned loan amount in integer.
        tenure_remaining (int, optional): Remaining loan tenure in months (e.g., if the original tenure was 25 years, enter 300 months directly, not as 25 * 12).
        existing_roi (float, optional): The current rate of interest on the loan.
        abhfl_roi (float, optional): The proposed rate of interest after transfer.
        month_of_disbursement (str, optional): The month of loan disbursement in %b-%y format (e.g., 'Aug-23').
        """
            ),
            StructuredTool.from_function(
                func=self.generate_salespitch,
                description="Function provide a personalized sales pitch recommendation and solution for an ABHFL home loan based on the customer information"
            ),
            StructuredTool.from_function(
                func=self.all_ABHFL_product_loan_information,
                description="Function to provide all information of ABHFL home loan"
            ),
        ]

        llm_with_tools = self.client.bind_tools(tools)
        # Check if we need to reset the SystemMessage
        if ABHFL.is_sales_pitch_active and ABHFL.is_function_calling == 11:
            ABHFL.is_sales_pitch_active = False  # Reset the flag
            print(self.message)
            self.reset_system_message() 
        print(self.message)    
        MEMORY_KEY = "chat_history"
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """You are a key figure at Aditya Birla Housing Finance Limited (ABHFL), but you have only limited information about the company. """),
                MessagesPlaceholder(variable_name=MEMORY_KEY),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        max_response_tokens = 250
        token_limit = 8000
        # Helper function to calculate total tokens in the messages
        def calculate_token_length(messages):
            tokens_per_message = 3
            tokens_per_name = 1
            # encoding = tiktoken.get_encoding(self.ENCODING)
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-0613")
            num_tokens = 0
            print(len(messages))
            for message in messages:
                # print(message.content)
                num_tokens += tokens_per_message
                # for value in message.content:
                #     print(value)
                num_tokens += len(encoding.encode(message.content))
                    # if key == "name":
                    #     num_tokens += tokens_per_name
            num_tokens += 3 
            print(num_tokens) # every reply is primed with <|start|>assistant<|message|>
            return num_tokens

        # Helper function to ensure message length is within limits
        def ensure_message_length_within_limit(message):
            # print("Lenth Function Called",messages[0])
            messages = self.message
            conv_history_tokens = calculate_token_length(self.message)
            
            while conv_history_tokens + max_response_tokens >= token_limit:
                print("Conv History", conv_history_tokens)
                if len(self.message) > 1:
                    del self.message[1]  # Remove the oldest message
                    conv_history_tokens = calculate_token_length(self.message)
        with get_openai_callback() as cb:
            try:
                
                ensure_message_length_within_limit(self.message)  # Reserve some tokens for functions and overhead
                # for chunk in agent_executor.astream_events(
                #     {"input": user_input, "chat_history": self.message}, version="v1"
                # ):
                #     yield chunk
                response = agent_executor.invoke({"input": user_input, "chat_history": self.message})
                
                return response["output"]

            except Exception as e:
                error_message = f"An error occurred: {e}"
                print(error_message)
                return error_message
            print("Token : ",cb)


                
# def iter_over_async(ait, loop):
#     ait = ait.__aiter__()
#     async def get_next():
#         try: obj = await ait.__anext__(); return False, obj
#         except StopAsyncIteration: return True, None
#     while True:
#         done, obj = loop.run_until_complete(get_next())
#         if done: break
#         yield obj        


# ob1 = ABHFL()
# while True:
#     if len(ob1.message) == 0:
#         with open("prompts\main_prompt2.txt", "r", encoding="utf-8") as f:
#             text = f.read()
#         ob1.message.append(SystemMessage(content=f"{text}"))
            

#     question = input("Please Enter a Query: ")
#     if question == "end":
#         break

#     openapiresponse = ob1.run_conversation(question)
#     print(openapiresponse)
        

#     ob1.message.append(AIMessage(content=f"{openapiresponse}"))
#     # print(ob1.message)


