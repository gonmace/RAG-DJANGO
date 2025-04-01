from django.db import models

class State(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)
    messages = models.JSONField(default=list)
    summary = models.JSONField(default=str)
    token_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State: {self.conversation_id}"