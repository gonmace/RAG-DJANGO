from django.urls import path
from . import views

app_name = 'embeddings'

urlpatterns = [
    path('crear/', views.add_document, name='crear'),
    path('listar/', views.listar_embeddings, name='listar'),
    path('eliminar/', views.eliminar_embeddings, name='eliminar'),
    path('actualizar/', views.actualizar_embedding, name='actualizar'),
    path('MDTitles/', views.split_documents_view, name='MDTitles'),
    path('MDSubdivide/', views.subdivide_documents_view, name='MDSubdivide'),
    path('createMDtitles/', views.create_embeddings_MDtitles, name='create_embeddings_MDtitles'),
    path('createMDsubdivide/', views.create_embeddings_MDsubdivide, name='create_embeddings_MDsubdivide'),
    path('similaridad/', views.similaridad_view, name='similaridad'),
]
