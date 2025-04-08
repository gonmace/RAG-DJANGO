from django.apps import AppConfig


class RagLegalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag_legal'

    def ready(self):
        import rag_legal.signals
