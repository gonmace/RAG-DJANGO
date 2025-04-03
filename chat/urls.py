from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path("legal/", views.chat_legal, name="chat_legal"),
] 