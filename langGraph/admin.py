from django.contrib import admin
from django.db import connection
import json

from .models import RagLegal

@admin.register(RagLegal)
class RagLegalAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'key', 'created_at', 'updated_at', 'get_formatted_value')
    search_fields = ('prefix', 'key')
    list_filter = ('prefix',)

    def get_formatted_value(self, obj):
        try:
            # Si el valor ya es un diccionario, no necesita ser parseado
            if isinstance(obj.value, dict):
                value = obj.value
            else:
                # Si es una cadena, intentamos parsearla
                value = json.loads(obj.value)
            
            queries = value.get('query', [])
            context = value.get('context', '')
            doc_count = len(context.split('<document>')) - 1 if context else 0
            
            return f"Queries: {len(queries)} | Docs: {doc_count}"
        except json.JSONDecodeError as e:
            return f"Error JSON: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    get_formatted_value.short_description = 'Resumen del contenido'
