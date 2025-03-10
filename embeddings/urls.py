from django.urls import path
from . import views

app_name = 'embeddings'

urlpatterns = [
    path('crear/', views.add_document, name='crear'),
    path('listar/', views.listar_embeddings, name='listar'),
    path('eliminar/', views.eliminar_embeddings, name='eliminar'),
    path('actualizar/', views.actualizar_embedding, name='actualizar'),
    path('splitters/', views.split_documents_view, name='splitters'),
    path('create/', views.create_embeddings, name='create_embeddings'),
    path('similaridad/', views.similaridad_view, name='similaridad'),
]
