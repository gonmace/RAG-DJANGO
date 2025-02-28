from django.urls import path
from . import views

app_name = 'embeddings'
urlpatterns = [
    path('crear/', views.crear_embedding, name='crear'),
]
