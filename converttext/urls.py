from django.urls import path
from . import views

app_name = 'converttext'
urlpatterns = [
    path('', views.convert_text, name='convert_text'),
    path('convert_pdf/', views.convert_pdf, name='convert_pdf'),
    path('convert_epub/', views.convert_epub, name='convert_epub'),
    path('convert_html/', views.convert_html, name='convert_html'),
    path('process_titles/', views.process_titles, name='process_titles'),
    path('change_tags/', views.change_tags, name='change_tags'),
    path('add_line_breaks/', views.add_line_breaks, name='add_line_breaks'),
    path('group_paragraphs/', views.group_paragraphs, name='group_paragraphs'),
]
