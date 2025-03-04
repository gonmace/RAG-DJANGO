from django.urls import path
from . import views

app_name = 'converttext'
urlpatterns = [
    path('', views.convert_text, name='convert_text'),
    path('pdf/', views.convert_pdf, name='convert_pdf'),
    path('epub/', views.convert_epub, name='convert_epub'),
    path('html/', views.convert_html, name='convert_html'),
]
