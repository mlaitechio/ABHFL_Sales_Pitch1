from rest_framework import serializers
from .models import  History , ChatSession, ChatMessage


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'
        # fields = ['session_id', 'user_id', 'created_on']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        # fields = ['session', 'message', 'answer', 'created_on']