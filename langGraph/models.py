from django.db import models
from django.utils import timezone

class GraphState(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    thread_id = models.CharField(max_length=255, unique=True)
    state = models.JSONField()  # Guarda el estado del grafo en formato JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['thread_id']),
            models.Index(fields=['user', 'thread_id']),
        ]
    
    def __str__(self):
        return f"GraphState for user {self.user.username} and thread {self.thread_id}"
    
    def update_state(self, new_state: dict) -> None:
        """
        Actualiza el estado del grafo con nuevos datos.
        """
        self.state.update(new_state)
        self.updated_at = timezone.now()
        self.save()
    
    def get_state(self) -> dict:
        """
        Retorna el estado actual del grafo.
        """
        return self.state
    
    @classmethod
    def create_or_update(cls, user, thread_id: str, state: dict) -> 'GraphState':
        """
        Crea un nuevo estado o actualiza uno existente.
        """
        graph_state, created = cls.objects.update_or_create(
            thread_id=thread_id,
            defaults={
                'user': user,
                'state': state,
                'is_active': True
            }
        )
        return graph_state
    
    def deactivate(self) -> None:
        """
        Marca el estado como inactivo.
        """
        self.is_active = False
        self.save()

