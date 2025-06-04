from rest_framework import serializers
from .models import  History , ChatSession, ChatMessage , Bookmark , Evaluation


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'
        # fields = ['session_id', 'user_id', 'created_on']

# class ChatMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ChatMessage
#         fields = '__all__'
#         # fields = ['session', 'message', 'answer', 'created_on']

class ChatMessageSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'input_prompt',
            'output',
            'ques_id',
            'input_prompt_timestamp',
            'output_timestamp',
            'created_on',
            'feedback',
            'select_feedback_response',
            'additional_comments',
            'session',
            'score',  # Include the new field
        ]

    def get_score(self, obj):
        evaluation = Evaluation.objects.filter(ques_id=obj.ques_id).first()
        return evaluation.score if evaluation else None
class BookMarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ['id', 'session', 'created_on']

class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = '__all__'
