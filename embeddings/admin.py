from django.contrib import admin
from .models import Embedding

@admin.register(Embedding)
class EmbeddingAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion', 'procesado')
    list_filter = ('procesado', 'fecha_creacion')
    search_fields = ('nombre',)


