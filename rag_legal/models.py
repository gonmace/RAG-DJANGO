from django.db import models
from django.contrib.auth.models import User

class State(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)
    messages = models.JSONField(default=list)
    summary = models.JSONField(default=str)
    token_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State: {self.conversation_id}"
    
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # 'user' o 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.role} - {self.user.username} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
    
    
    