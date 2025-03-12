from django.urls import path
from . import views

app_name = 'langGraph'

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
    path('process-message/', views.process_message, name='process_message'),
] 