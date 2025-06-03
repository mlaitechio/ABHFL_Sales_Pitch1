# Create your models here.
from django.db import models
import uuid
from langchain.schema import SystemMessage, AIMessage, HumanMessage


class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=100, default=" ")
    is_activate = models.BooleanField(default=True)
    session_name = models.CharField(max_length=255, blank=True, null=True)  # New field for session name
    
    def __str__(self):
        return f"Chat Session {self.session_id} for User {self.user_id}"
    

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    input_prompt = models.TextField()
    output = models.TextField(blank=True, null=True)
    ques_id = models.TextField(blank=True) # Unique question ID
    input_prompt_timestamp = models.TextField(blank=True)
    output_timestamp = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True, null=True)
    select_feedback_response = models.TextField(blank=True, null=True)
    additional_comments = models.TextField(blank=True, null=True)

class Bookmark(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='bookmarks')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='bookmarks', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bookmark for Session {self.session.session_id}, Message ID: {self.message.id}"

class History(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='chat_history')
    messages = models.JSONField(default=list)  # Storing chat history as a JSON array
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {self.timestamp}"

    def get_messages(self):
        # Deserialize JSON messages into LangChain message objects
        return [self.deserialize_message(msg) for msg in self.messages]

    def set_messages(self, messages):
        # Serialize LangChain message objects into JSON-serializable dictionaries
        self.messages = [self.serialize_message(msg) for msg in messages]

    @staticmethod
    def serialize_message(message):
        if isinstance(message, SystemMessage):
            return {'role': 'system', 'content': message.content}
        elif isinstance(message, AIMessage):
            return {'role': 'assistant', 'content': message.content}
        elif isinstance(message, HumanMessage):
            return {'role': 'user', 'content': message.content}
        else:
            raise ValueError(f"Unknown message type: {type(message)}")

    @staticmethod
    def deserialize_message(message):
        role = message['role']
        content = message['content']
        if role == 'system':
            return SystemMessage(content=content)
        elif role == 'assistant':
            return AIMessage(content=content)
        elif role == 'user':
            return HumanMessage(content=content)
        else:
            raise ValueError(f"Unknown message role: {role}")
        

        
# New Evaluation model for storing the evaluation data
class Evaluation(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='evaluations')
    ques_id = models.TextField(blank=True)
    input = models.TextField(blank=True)
    input_token_count = models.TextField(blank=True)
    output_token_count = models.TextField(blank=True)
    output = models.TextField(blank=True)
    score = models.FloatField(blank=True, null=True)  # Overall performance score (0.0 to 1.0)
    step_efficiency = models.FloatField(blank=True, null=True)  # Efficiency score (0.0 to 1.0)
    used_tools = models.JSONField(blank=True, null=True)  # List of tools used in the trajectory
    tool_usage_count = models.JSONField(blank=True, null=True)  # Dictionary of tool names to usage count
    tool_confidence = models.JSONField(blank=True, null=True)  # Dictionary of tool names to confidence scores
    tool_confidence_avg = models.FloatField(blank=True, null=True)  # Average confidence score for tools
    total_steps = models.IntegerField(blank=True, null=True)  # Total steps in the trajectory
    redundant_steps = models.JSONField(blank=True, null=True)  # List of redundant step numbers
    tool_selection_quality = models.FloatField(blank=True, null=True)  # Tool selection quality (0.0 to 1.0)
    final_answer_helpful = models.BooleanField(blank=True, null=True)  # Whether the final answer was helpful
    reasoning_quality = models.FloatField(blank=True, null=True)  # Quality of the reasoning (0.0 to 1.0)
    reasoning = models.TextField(blank=True, null=True)  # Detailed reasoning for the evaluation

    def __str__(self):
        return f"Evaluation for Session {self.session.session_id}, Score: {self.score}"

    # Method to store the result from the evaluation logic (StepNecessityEvaluator)
    @classmethod
    def from_evaluation(cls, session: ChatSession, evaluation_data: dict):
        """
        Create an Evaluation instance from the data returned by the evaluator.
        """
        return cls.objects.create(
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
