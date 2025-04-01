from django.urls import path
from .views import RAGLegalView

urlpatterns = [
    path("api/v1/legal/", RAGLegalView.as_view(), name="chat_rag_legal"),
] 