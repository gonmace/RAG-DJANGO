from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text
import os
import tempfile
import logging
import re
import fitz  # PyMuPDF
from .services import (
    pdf_a_html,
    procesar_titulos,
    cambiar_etiquetas,
    agregar_saltos_linea,
    agrupar_parrafos,
    html_a_markdown,
    eliminar_lineas,
    procesar_saltos_linea,
    eliminar_duplicados
)

logger = logging.getLogger(__name__)

def convert_text(request):
    return render(request, 'converttext.html')

def get_markdown_filename(original_filename):
    """Función auxiliar para cambiar la extensión a .md"""
    name_without_ext = os.path.splitext(original_filename)[0]
    return f"{name_without_ext}.md"

def clean_text_for_llm(text):
    """Función para limpiar el texto de elementos innecesarios para LLM"""
    # Eliminar enlaces
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Eliminar código
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Eliminar imágenes
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
    
    # Eliminar anclas HTML
    text = re.sub(r'<a[^>]*>([^<]*)</a>', r'\1', text)
    
    # Eliminar otras etiquetas HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Eliminar URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Eliminar caracteres especiales y emojis
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    
    # Preservar números de página y encabezados
    text = re.sub(r'(## Página \d+)\n', r'\1\n\n', text)
    
    # Preservar espacios entre párrafos
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Preservar espacios al inicio de líneas
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()

def clean_text(text):
    """Función para limpiar espacios múltiples y normalizar el texto"""
    # Eliminar espacios múltiples
    text = ' '.join(text.split())
    # Eliminar espacios antes de signos de puntuación
    text = re.sub(r'\s+([.,;:?!])', r'\1', text)
    return text.strip()

def clean_pdf_text(text):
    """Función específica para limpiar texto de PDF"""
    # Eliminar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    # Eliminar espacios antes de signos de puntuación
    text = re.sub(r'\s+([.,;:?!])', r'\1', text)
    # Eliminar espacios después de números seguidos de punto
    text = re.sub(r'(\d+\.)\s+', r'\1', text)
    # Eliminar espacios antes de punto cuando hay un número
    text = re.sub(r'\s+\.(\d+)', r'.\1', text)
    return text.strip()

@csrf_exempt
def convert_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        eliminar_tablas = request.POST.get('eliminar_tablas') == 'on'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name

        try:
            # Crear un archivo temporal para el HTML de salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
                temp_html_path = temp_html.name
            
            # Convertir PDF a HTML usando el servicio
            pdf_a_html(temp_pdf_path, temp_html_path, eliminar_tablas)
            
            # Leer el contenido HTML generado
            with open(temp_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(pdf_file.name)[0]}.html"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante la conversión: {str(e)}", status=500)
        finally:
            os.unlink(temp_pdf_path)
            if 'temp_html_path' in locals():
                os.unlink(temp_html_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo PDF", status=400)

@csrf_exempt
def convert_epub(request):
    if request.method == 'POST' and request.FILES.get('epub_file'):
        epub_file = request.FILES['epub_file']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_epub:
            for chunk in epub_file.chunks():
                temp_epub.write(chunk)
            temp_epub_path = temp_epub.name

        try:
            book = epub.read_epub(temp_epub_path)
            html_content = []
            
            # Extraer el contenido HTML de cada documento
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    html_content.append(content)
            
            # Unir todo el contenido HTML
            final_html = "".join(html_content)
            
            # Convertir HTML a Markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.ignore_emphasis = False
            h.body_width = 0  # No limitar el ancho del texto
            
            markdown_content = h.handle(final_html)
            
            # Limpiar el texto para LLM
            cleaned_content = clean_text_for_llm(markdown_content)
            
            # Enviar el archivo Markdown
            response = HttpResponse(cleaned_content, content_type='text/markdown')
            response['Content-Disposition'] = f'attachment; filename="{get_markdown_filename(epub_file.name)}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante la conversión: {str(e)}", status=500)
        finally:
            os.unlink(temp_epub_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo ePub", status=400)

@csrf_exempt
def process_titles(request):
    if request.method == 'POST' and request.FILES.get('html_file'):
        html_file = request.FILES['html_file']
        title_keywords = [keyword.strip() for keyword in request.POST.get('title_keywords', '').split(',')]
        additional_lines = int(request.POST.get('additional_lines', 0))
        html_tag = request.POST.get('html_tag', 'h2')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
            for chunk in html_file.chunks():
                temp_html.write(chunk)
            temp_html_path = temp_html.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_output:
                temp_output_path = temp_output.name
            
            # Procesar títulos
            procesar_titulos(temp_html_path, temp_output_path, title_keywords, additional_lines, html_tag)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="{html_tag}_{html_file.name}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante el procesamiento: {str(e)}", status=500)
        finally:
            os.unlink(temp_html_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)

@csrf_exempt
def change_tags(request):
    if request.method == 'POST' and request.FILES.get('html_file'):
        html_file = request.FILES['html_file']
        source_tag = request.POST.get('source_tag')
        target_tag = request.POST.get('target_tag')
        keywords = [keyword.strip() for keyword in request.POST.get('keyword', '').split(',')]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
            for chunk in html_file.chunks():
                temp_html.write(chunk)
            temp_html_path = temp_html.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_output:
                temp_output_path = temp_output.name
            
            # Cambiar etiquetas
            cambiar_etiquetas(temp_html_path, temp_output_path, keywords, source_tag, target_tag)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="tags_changed_{html_file.name}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante el cambio de etiquetas: {str(e)}", status=500)
        finally:
            os.unlink(temp_html_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)

@csrf_exempt
def add_line_breaks(request):
    if request.method == 'POST' and request.FILES.get('html_file'):
        html_file = request.FILES['html_file']
        keywords = [keyword.strip() for keyword in request.POST.get('keywords', '').split(',')]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
            for chunk in html_file.chunks():
                temp_html.write(chunk)
            temp_html_path = temp_html.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_output:
                temp_output_path = temp_output.name
            
            # Agregar saltos de línea
            procesar_saltos_linea(temp_html_path, temp_output_path, keywords)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="line_breaks_{html_file.name}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante el agregado de saltos de línea: {str(e)}", status=500)
        finally:
            os.unlink(temp_html_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)

@csrf_exempt
def group_paragraphs(request):
    if request.method == 'POST' and request.FILES.get('html_file'):
        html_file = request.FILES['html_file']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
            for chunk in html_file.chunks():
                temp_html.write(chunk)
            temp_html_path = temp_html.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_output:
                temp_output_path = temp_output.name
            
            # Agrupar párrafos
            agrupar_parrafos(temp_html_path, temp_output_path)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="grouped_{html_file.name}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante el agrupamiento de párrafos: {str(e)}", status=500)
        finally:
            os.unlink(temp_html_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)

@csrf_exempt
def convert_html(request):
    if request.method == 'POST' and request.FILES.get('html_file'):
        html_file = request.FILES['html_file']
        title = request.POST.get('title', '').strip()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
            for chunk in html_file.chunks():
                temp_html.write(chunk)
            temp_html_path = temp_html.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as temp_output:
                temp_output_path = temp_output.name
            
            # Convertir HTML a Markdown
            html_a_markdown(temp_html_path, temp_output_path)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Agregar el título al inicio si se proporcionó uno
            if title:
                markdown_content = f"# {title}\n\n{markdown_content}"
                # Usar el título como nombre del archivo, limpiando caracteres especiales
                filename = re.sub(r'[<>:"/\\|?*]', '_', title)
                filename = re.sub(r'\s+', '_', filename)
                filename = f"{filename}.md"
            else:
                filename = f"{os.path.splitext(html_file.name)[0]}.md"
            
            response = HttpResponse(markdown_content, content_type='text/markdown')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante la conversión a Markdown: {str(e)}", status=500)
        finally:
            os.unlink(temp_html_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)

@csrf_exempt
def eliminar_lineas_view(request):
    if request.method == 'POST' and request.FILES.get('html_file'):
        html_file = request.FILES['html_file']
        texto_a_eliminar = request.POST.get('texto_a_eliminar', '').strip()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
            for chunk in html_file.chunks():
                temp_html.write(chunk)
            temp_html_path = temp_html.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_output:
                temp_output_path = temp_output.name
            
            # Eliminar líneas
            eliminar_lineas(temp_html_path, temp_output_path, texto_a_eliminar)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="dellines_{html_file.name}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante el procesamiento: {str(e)}", status=500)
        finally:
            os.unlink(temp_html_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)

@csrf_exempt
def remove_duplicate_lines(request):
    if request.method == 'POST' and request.FILES.get('md_file'):
        md_file = request.FILES['md_file']
        min_chars = int(request.POST.get('min_chars', 100))
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as temp_md:
            for chunk in md_file.chunks():
                temp_md.write(chunk)
            temp_md_path = temp_md.name

        try:
            # Crear un archivo temporal para la salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as temp_output:
                temp_output_path = temp_output.name
            
            # Eliminar líneas duplicadas
            eliminar_duplicados(temp_md_path, temp_output_path, min_chars)
            
            # Leer el contenido procesado
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            response = HttpResponse(md_content, content_type='text/markdown')
            response['Content-Disposition'] = f'attachment; filename="{md_file.name}"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante la eliminación de líneas duplicadas: {str(e)}", status=500)
        finally:
            os.unlink(temp_md_path)
            if 'temp_output_path' in locals():
                os.unlink(temp_output_path)
    
    return HttpResponse("Error: No se proporcionó ningún archivo Markdown", status=400) 