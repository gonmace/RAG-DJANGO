from django.db import models
from django.contrib.auth.models import User

class State(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)
    messages = models.JSONField(default=list)
    summary = models.JSONField(default=str)
    token_cost = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State: {self.conversation_id}"
    
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)
    cost = models.FloatField(default=0, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.role} - {self.user.username} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Solo acumula si es un mensaje nuevo
        super().save(*args, **kwargs)  # Guardar primero para tener ID
        if is_new and self.cost:  # Solo acumula si hay cost > 0
            token_cost, created = TokenCost.objects.get_or_create(user=self.user)
            token_cost.total_cost += self.cost
            token_cost.save()

class TokenCost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credits = models.FloatField(default=0.5)
    total_cost = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"TokenCost: {self.user.username} - {self.total_cost}"
    
    