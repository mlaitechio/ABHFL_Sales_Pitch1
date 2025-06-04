from typing import Any, Optional, Sequence, Tuple

from langchain.chains import LLMChain
from langchain.evaluation import AgentTrajectoryEvaluator
from langchain_core.agents import AgentAction
from langchain_openai import ChatOpenAI , AzureChatOpenAI
import os
import json
from .models import Evaluation, ChatSession

class StepNecessityEvaluator(AgentTrajectoryEvaluator):
    """Evaluate the perplexity of a predicted string."""

    def __init__(self) -> None:
        API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        Completion_Model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        llm = AzureChatOpenAI(
                api_key=API_KEY,
                api_version="2023-07-01-preview",
                azure_endpoint=RESOURCE_ENDPOINT,
                azure_deployment=Completion_Model,
            )
        valid_tools = self.get_valid_tool_names()
        valid_tool_list = ", ".join(sorted(valid_tools)) or "No tools available."
        template = """You are evaluating whether an AI agent followed an efficient and effective reasoning process to answer the input question. Based on the following step-by-step trajectory, return a structured JSON object with the following fields:

- "score": A float between 0.0 and 1.0 indicating the overall performance of the agent.
- "step_efficiency": A float (0.0 to 1.0) representing how efficient the agent was in using the fewest necessary steps.
- "used_tools": A list of all tools or agents used in the trajectory.
- "tool_usage_count": A dictionary of tool names to the number of times each tool was used.
- "tool_confidence": A dictionary of tool names to confidence scores (0.0 to 1.0) indicating how appropriately each tool was used.
- "tool_confidence_avg": A float average of all confidence scores.
- "total_steps": Total number of steps in the trajectory.
- "redundant_steps": A list of step numbers that could have been omitted or were not useful.
- "tool_selection_quality": A float (0.0 to 1.0) reflecting whether the best tools were chosen for the task.
- "final_answer_helpful": A boolean indicating if the final answer was genuinely helpful.
- "reasoning_quality": A float (0.0 to 1.0) judging the clarity, logic, and completeness of the reasoning.
- "reasoning": A detailed explanation addressing:
     Was the final answer helpful?
    Were the tools used in a logical and appropriate order?
     Were any tools used inefficiently or unnecessarily?
    Were there better tools that could have been used?
    Was the reasoning coherent and informative?
    
----------- 
Available tools: {valid_tool_list}

DATA
------
Steps:
{trajectory}
------
Input:
{input}

Output:
{output}

Evaluation (return as JSON only):"""
        self.chain = LLMChain.from_string(llm, template)

    def _evaluate_agent_trajectory(
        self,
        *,
        prediction: str,
        input: str,
        session_id: str,
        ques_id : str,
        agent_trajectory: Sequence[Tuple[AgentAction, str]],
        reference: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        vals = []
        used_tools = set()
        tool_confidence = {}
        input_token = kwargs.get("input_token", "")
        output_token = kwargs.get("output_token", "")
        for i, (action, observation) in enumerate(agent_trajectory):
            vals.append(f"{i}: Action=[{action.tool}] returned observation = [{observation}]")
            tool_name = action.tool
            used_tools.add(tool_name)
            confidence = getattr(action, "confidence", 1.0)
            tool_confidence[tool_name] = max(tool_confidence.get(tool_name, 0.0), confidence)

        trajectory_str = "\n".join(vals)
        total_steps = len(agent_trajectory)

        # Get valid tools from product_description1.json
        valid_tool_list = ", ".join(sorted(self.get_valid_tool_names())) or "No tools available."

        # Run evaluation chain
        print(trajectory_str)
        response = self.chain.invoke({
            "trajectory": trajectory_str,
            "input": input,
            "output":prediction,
            "valid_tool_list": valid_tool_list
        }, **kwargs)
        
        question = response["input"]
        answer = response["output"]
        print("Response: " ,  response)
        print("Question:", question)
        # Parse structured JSON block
        try:
            json_block = response["text"].strip().split("```json")[-1].split("```")[0].strip()
            evaluation = json.loads(json_block)
        except Exception:
            # Fallback if parsing fails
            evaluation = {}

        # Ensure all expected fields are present with defaults
        default_evaluation = {
            "input" : question,
            "output" :answer,
            "ques_id" : ques_id,
            "score": 0.0,
            "input_token_count": input_token,
            "output_token_count": output_token,
            "step_efficiency": 0.0,
            "used_tools": list(used_tools),
            "tool_usage_count": {},
            "tool_confidence": tool_confidence,
            "tool_confidence_avg": (
                sum(tool_confidence.values()) / len(tool_confidence) if tool_confidence else 0.0
            ),
            "total_steps": total_steps,
            "redundant_steps": [],
            "tool_selection_quality": 0.0,
            "final_answer_helpful": False,
            "reasoning_quality": 0.0,
            "reasoning": response,
        }

        for key, default in default_evaluation.items():
            evaluation.setdefault(key, default)

        # Ensure required fields are always populated
        evaluation.setdefault("used_tools", list(used_tools))
        evaluation.setdefault("tool_confidence", tool_confidence)
        evaluation.setdefault("total_steps", total_steps)
        evaluation.setdefault("reasoning", response)

        # Save the evaluation to the database
        self.save_evaluation_to_db(session_id, evaluation)

        return evaluation
    
    def get_valid_tool_names(self):
        try:
            with open("prompts/product_descriptions1.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.keys())
        except Exception:
            return set()


    def save_evaluation_to_db(self, session, evaluation_data: dict):
        """
        This method saves the evaluation results to the database by creating an Evaluation record.
        """
        Evaluation.objects.create(
            session=session,
            score=evaluation_data.get('score', 0.0),
            step_efficiency=evaluation_data.get('step_efficiency', 0.0),
            used_tools=evaluation_data.get('used_tools', []),
            tool_usage_count=evaluation_data.get('tool_usage_count', {}),
            tool_confidence=evaluation_data.get('tool_confidence', {}),
            tool_confidence_avg=evaluation_data.get('tool_confidence_avg', 0.0),
            total_steps=evaluation_data.get('total_steps', 0),
            redundant_steps=evaluation_data.get('redundant_steps', []),
            tool_selection_quality=evaluation_data.get('tool_selection_quality', 0.0),
            final_answer_helpful=evaluation_data.get('final_answer_helpful', False),
            reasoning_quality=evaluation_data.get('reasoning_quality', 0.0),
            reasoning=evaluation_data.get('reasoning', ''),
            input=evaluation_data.get('input', ''),
            output=evaluation_data.get('output', ''),
            ques_id=evaluation_data.get('ques_id', ''),
            input_token_count=evaluation_data.get('input_token_count', ''),
            output_token_count=evaluation_data.get('output_token_count', ''),
        )