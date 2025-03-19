from django.contrib import admin
from django.db import connection

from .models import Checkpoint

@admin.register(Checkpoint)
class CheckpointAdmin(admin.ModelAdmin):
    list_display = ('checkpoint_id', 'thread_id', 'get_timestamp', 'get_message_type', 'get_message_content')
    search_fields = ('checkpoint_id', 'thread_id')
    list_filter = ('thread_id',)  # Agregar filtro por thread_id
    readonly_fields = ('formatted_metadata', 'get_summary', 'get_step', 'get_timestamp', 'get_message_type', 'get_message_content')
    ordering = ('-checkpoint_id',)  # Ordenamiento inverso por defecto
    fieldsets = (
        ('Información Básica', {
            'fields': ('checkpoint_id', 'thread_id', 'get_timestamp', 'get_message_type')
        }),
        ('Mensaje', {
            'fields': ('get_message_content',),
            'classes': ('collapse',)
        }),
        ('Metadata Completo', {
            'fields': ('formatted_metadata',),
            'classes': ('collapse',)
        }),
    )

    def delete_selected_checkpoints(self, request, queryset):
        """Acción personalizada para borrar checkpoints y sus registros relacionados"""
        with connection.cursor() as cursor:
            for checkpoint in queryset:
                # Borrar registros relacionados en checkpoint_writes
                cursor.execute("DELETE FROM checkpoint_writes WHERE checkpoint_id = %s", [checkpoint.parent_checkpoint_id])
                # Borrar el registro en checkpoints
                cursor.execute("DELETE FROM checkpoints WHERE checkpoint_id = %s", [checkpoint.checkpoint_id])
        self.message_user(request, f"Se han borrado {queryset.count()} checkpoints y sus registros relacionados")
    delete_selected_checkpoints.short_description = "Borrar checkpoints seleccionados y sus registros relacionados"

    def get_actions(self, request):
        """Sobrescribe las acciones disponibles para eliminar la acción de borrado por defecto"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    actions = ['delete_selected_checkpoints']
