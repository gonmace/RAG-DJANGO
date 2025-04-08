from django.contrib import admin
from django.utils.html import format_html
from rag_legal.models import State, ChatMessage, TokenCost
from django.utils.timezone import localtime

class StateAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'created_at', 'updated_at', 'messages')
    readonly_fields = ('created_at', 'updated_at', 'formatted_messages', 'formatted_summary')
    
    def formatted_messages(self, obj):
        messages_html = []
        for msg in obj.messages:
            content = msg['kwargs']['content']
            msg_type = msg['kwargs']['type']
            messages_html.append(f'<div style="margin-bottom: 10px; padding: 10px; background-color: {"#4b4b4b" if msg_type == "human" else "#333333"}; border-radius: 5px;">')
            messages_html.append(f'<strong>{msg_type.upper()}:</strong><br>{content}')
            messages_html.append('</div>')
        return format_html(''.join(messages_html))
    formatted_messages.short_description = 'Mensajes'
    
    def formatted_summary(self, obj):
        if isinstance(obj.summary, str):
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', obj.summary)
        return format_html('<pre style="white-space: pre-wrap;">{}</pre>', str(obj.summary))
    formatted_summary.short_description = 'Resumen'
    

    
    fieldsets = (
        ('Información Básica', {
            'fields': ('conversation_id', 'created_at', 'updated_at')
        }),
        ('Conversación', {
            'fields': ('messages', 'formatted_messages'),
            # 'fields': ('formatted_messages',),
        }),
        ('Resumen', {
            'fields': ('summary', 'formatted_summary'),
            # 'fields': ('formatted_summary',),
        }),
        ('Información de Tokens', {
            'fields': ('token_cost',),
        }),
    )

admin.site.register(State, StateAdmin)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'content_preview', 'formatted_timestamp', 'cost')
    list_filter = ('role', 'user', 'timestamp')
    search_fields = ('content', 'user__username')
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        """Muestra una vista previa del contenido del mensaje"""
        return obj.content[:150] + '...' if len(obj.content) > 150 else obj.content
    content_preview.short_description = 'Contenido'
    
    def formatted_timestamp(self, obj):
        """Muestra la fecha y hora en formato corto"""
        dt = localtime(obj.timestamp)  # asegura que esté en la zona horaria local
        return dt.strftime('%H:%M:%S-%d/%m/%Y')  # Ejemplo: 07/04/2025 13:44:00
    formatted_timestamp.short_description = 'Hora-Fecha'

class TokenCostAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_cost', 'credits', 'formatted_created_at', 'formatted_updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    
    def formatted_created_at(self, obj):
        """Muestra la fecha y hora en formato corto"""
        dt = localtime(obj.created_at)  # asegura que esté en la zona horaria local
        return dt.strftime('%H:%M:%S - %d/%m/%y')  # Ejemplo: 07/04/2025 13:44:00
    formatted_created_at.short_description = 'Creado'
    
    def formatted_updated_at(self, obj):
        """Muestra la fecha y hora en formato corto"""
        dt = localtime(obj.updated_at)  # asegura que esté en la zona horaria local
        return dt.strftime('%H:%M:%S - %d/%m/%y')  # Ejemplo: 07/04/2025 13:44:00
    formatted_updated_at.short_description = 'Actualizado'

admin.site.register(TokenCost, TokenCostAdmin)