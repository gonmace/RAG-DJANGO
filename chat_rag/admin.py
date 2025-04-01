from django.contrib import admin
from django.utils.html import format_html
from chat_rag.models import State

class StateAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'formatted_messages', 'formatted_summary', 'formatted_token_info')
    
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
    
    def formatted_token_info(self, obj):
        if not obj.token_info:
            return format_html('<div style="padding: 10px; background-color: #4b4b4b; border-radius: 5px;">No hay información de tokens disponible</div>')
            
        try:
            token_info = obj.token_info
            cost = str(token_info['cost'])
            return format_html(
                '<div style="padding: 10px; background-color: #4b4b4b; border-radius: 5px;">'
                '<strong>Costo:</strong> ${}<br>'
                '<strong>Total Tokens:</strong> {}<br>'
                '<strong>Tokens de Prompt:</strong> {}<br>'
                '<strong>Tokens de Completado:</strong> {}'
                '</div>',
                cost,
                token_info['total_tokens'],
                token_info['prompt_tokens'],
                token_info['completion_tokens']
            )
        except (KeyError, TypeError, ValueError) as e:
            return format_html('<div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px;">Error al formatear la información de tokens: {}</div>', str(e))
    formatted_token_info.short_description = 'Información de Tokens'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('conversation_id', 'created_at', 'updated_at')
        }),
        ('Conversación', {
            # 'fields': ('messages', 'formatted_messages'),
            'fields': ('formatted_messages',),
        }),
        ('Resumen', {
            # 'fields': ('summary', 'formatted_summary'),
            'fields': ('formatted_summary',),
        }),
        ('Información de Tokens', {
            # 'fields': ('token_info', 'formatted_token_info'),
            'fields': ('formatted_token_info',),
        }),
    )

admin.site.register(State, StateAdmin)
