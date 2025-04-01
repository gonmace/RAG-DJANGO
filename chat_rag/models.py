from django.db import models

class State(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)
    messages = models.JSONField(default=list)      # Lista de mensajes
    summary = models.JSONField(default=dict)       # Puede ser texto o estructura
    token_info = models.JSONField(default=dict)    # Tokens y costos
    # state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State for conversation {self.conversation_id}"