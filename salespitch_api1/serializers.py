from rest_framework import serializers
from .models import  History , ChatSession, ChatMessage2


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'
        # fields = ['session_id', 'user_id', 'created_on']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage2
        fields = '__all__'
        # fields = ['session', 'message', 'answer', 'created_on']