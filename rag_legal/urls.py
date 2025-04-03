from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views import RAGLegalView

urlpatterns = [
    path("api/v1/legal/", csrf_exempt(RAGLegalView.as_view()), name="rag_legal"),
] 