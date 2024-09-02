from django.db import models
import uuid

    
# Create your models here.

class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Chat Session {self.session_id} for User {self.ip}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    answer = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

