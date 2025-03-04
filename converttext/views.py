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

@csrf_exempt
def convert_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        
        # Obtener los patrones y líneas del formulario
        chapter_patterns = [p.strip() for p in request.POST.get('chapter_patterns', '').split(',') if p.strip()]
        section_patterns = [p.strip() for p in request.POST.get('section_patterns', '').split(',') if p.strip()]
        chapter_lines = int(request.POST.get('chapter_lines', 0))
        section_lines = int(request.POST.get('section_lines', 0))
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name

        try:
            html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documento Convertido</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { 
            text-align: center;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 { 
            color: #cc7f38;
            margin-top: 20px;
            font-size: 1.5em;
            font-weight: bold;
        }
        h3 { 
            color: #345e4e;
            margin-top: 15px;
            font-size: 1.2em;
            font-weight: bold;
        }
        p { 
            text-align: justify;
            margin: 10px 0;
        }
        strong {
            font-weight: bold;
            color: #2c3e50;
        }
    </style>
</head>
<body>"""

            # Extraer el título del nombre del archivo
            title = os.path.splitext(pdf_file.name)[0]
            html_content += f"<h1>{title}</h1>\n"

            doc = fitz.open(temp_pdf_path)
            
            # Procesar cada página
            for page in doc:
                blocks = page.get_text("dict")["blocks"]
                i = 0
                while i < len(blocks):
                    block = blocks[i]
                    if "lines" in block:
                        for line in block["lines"]:
                            if "spans" in line:
                                current_line = []
                                line_text = ""
                                for span in line["spans"]:
                                    text = span.get("text", "").strip()
                                    if not text:
                                        continue
                                    line_text += text + " "
                                    current_line.append(text)
                                
                                line_text = line_text.strip()
                                
                                # Verificar si la línea coincide con algún patrón de capítulo
                                is_chapter = any(pattern in line_text.upper() for pattern in chapter_patterns)
                                # Verificar si la línea coincide con algún patrón de sección
                                is_section = any(pattern in line_text.upper() for pattern in section_patterns)
                                
                                if is_chapter:
                                    # Procesar líneas adicionales para capítulos
                                    additional_lines = []
                                    for _ in range(chapter_lines):
                                        i += 1
                                        if i < len(blocks) and "lines" in blocks[i]:
                                            for add_line in blocks[i]["lines"]:
                                                if "spans" in add_line:
                                                    add_text = " ".join(span.get("text", "").strip() for span in add_line["spans"])
                                                    if add_text:
                                                        additional_lines.append(add_text)
                                    
                                    if additional_lines:
                                        html_content += f"<h2>{line_text}: {' '.join(additional_lines)}</h2>\n"
                                    else:
                                        html_content += f"<h2>{line_text}</h2>\n"
                                    current_line = []
                                
                                elif is_section:
                                    # Procesar líneas adicionales para secciones
                                    additional_lines = []
                                    for _ in range(section_lines):
                                        i += 1
                                        if i < len(blocks) and "lines" in blocks[i]:
                                            for add_line in blocks[i]["lines"]:
                                                if "spans" in add_line:
                                                    add_text = " ".join(span.get("text", "").strip() for span in add_line["spans"])
                                                    if add_text:
                                                        additional_lines.append(add_text)
                                    
                                    if additional_lines:
                                        html_content += f"<h3>{line_text}: {' '.join(additional_lines)}</h3>\n"
                                    else:
                                        html_content += f"<h3>{line_text}</h3>\n"
                                    current_line = []
                                
                                else:
                                    # Si no es título, procesar cada span individualmente
                                    html_content += "<p>"
                                    for span in line["spans"]:
                                        text = span.get("text", "").strip()
                                        if not text:
                                            continue
                                        
                                        font = span.get("font", "").lower()
                                        # Detectar negrillas
                                        if any(bold in font for bold in ['bold', 'negrita', 'negrita']):
                                            text = f"<strong>{text}</strong>"
                                        html_content += text + " "
                                    html_content += "</p>\n"
                    i += 1
            
            doc.close()
            html_content += "</body>\n</html>"
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(pdf_file.name)[0]}.html"'
            return response
            
        except Exception as e:
            return HttpResponse(f"Error durante la conversión: {str(e)}", status=500)
        finally:
            os.unlink(temp_pdf_path)
    
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
def convert_html(request):
    logger.info("Iniciando conversión de HTML")
    if request.method == 'POST':
        logger.info(f"Método POST recibido. FILES: {request.FILES}")
        if request.FILES.get('html_file'):
            html_file = request.FILES['html_file']
            logger.info(f"Archivo HTML recibido: {html_file.name}")
            
            # Obtener los selectores CSS (opcionales)
            title_selector = request.POST.get('title_selector')  # Selector para el título
            special_selector = request.POST.get('special_selector')  # Selector para secciones especiales
            chapter_selector = request.POST.get('chapter_selector')  # Selector para capítulos
            section_selector = request.POST.get('section_selector')  # Selector para secciones
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
                for chunk in html_file.chunks():
                    temp_html.write(chunk)
                temp_html_path = temp_html.name
                logger.info(f"Archivo temporal creado en: {temp_html_path}")

            try:
                with open(temp_html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                markdown_content = []
                chapter_count = 1
                
                # Procesar título directamente del campo
                if title_selector:
                    title_text = title_selector.strip()
                    if title_text:
                        # Agregar el título en la primera línea
                        markdown_content = [f"# {title_text}"]
                
                # Procesar todos los elementos en orden
                processed_elements = set()
                
                # Función auxiliar para verificar si un elemento coincide con un selector
                def matches_selector(element, selector):
                    if not selector:
                        return False
                    try:
                        # Verificar si el elemento actual coincide con el selector
                        return element.name in selector.split() or element.get('class') and any(cls in selector for cls in element.get('class'))
                    except Exception as e:
                        logger.error(f"Error al procesar selector CSS '{selector}': {str(e)}")
                        return False
                
                # Procesar elementos en orden
                for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'div', 'section', 'article']):
                    if element in processed_elements:
                        continue
                        
                    # Procesar secciones especiales
                    if special_selector and matches_selector(element, special_selector):
                        text = element.get_text().strip().lower()
                        if any(keyword in text for keyword in ['glosario', 'índice', 'introducción', 'prólogo', 'prefacio']):
                            markdown_content.append(f"## {element.get_text().strip()}\n")
                            processed_elements.add(element)
                            continue
                    
                    # Procesar capítulos
                    if chapter_selector and matches_selector(element, chapter_selector):
                        text = element.get_text().strip()
                        if text and not any(keyword in text.lower() for keyword in ['glosario', 'índice', 'introducción', 'prólogo', 'prefacio']):
                            markdown_content.append(f"## {chapter_count}: {text}\n")
                            chapter_count += 1
                            processed_elements.add(element)
                            continue
                    
                    # Procesar secciones
                    if section_selector and matches_selector(element, section_selector):
                        text = element.get_text().strip()
                        if text and not any(keyword in text.lower() for keyword in ['glosario', 'índice', 'introducción', 'prólogo', 'prefacio']):
                            markdown_content.append(f"### {text}\n")
                            processed_elements.add(element)
                            continue
                    
                    # Procesar contenido normal
                    if element.name in ['p', 'div', 'section', 'article']:
                        text = element.get_text().strip()
                        if text and element not in processed_elements:
                            markdown_content.append(text)
                            processed_elements.add(element)
                        elif not text and element not in processed_elements:
                            markdown_content.append("")  # Agregar línea vacía
                            processed_elements.add(element)
                
                # Unir el contenido preservando líneas vacías
                final_content = "\n".join(markdown_content)
                # Asegurar que no haya más de dos líneas vacías consecutivas
                # final_content = re.sub(r'\n{3,}', '\n\n', final_content)
                
                logger.info("Conversión de HTML completada exitosamente")
                response = HttpResponse(final_content, content_type='text/markdown')
                response['Content-Disposition'] = f'attachment; filename="{get_markdown_filename(html_file.name)}"'
                return response
                
            except Exception as e:
                logger.error(f"Error durante la conversión del HTML: {str(e)}")
                return HttpResponse(f"Error durante la conversión: {str(e)}", status=500)
            finally:
                os.unlink(temp_html_path)
                logger.info("Archivo temporal eliminado")
        else:
            logger.warning("No se encontró el archivo HTML en la solicitud")
    else:
        logger.warning(f"Método no permitido: {request.method}")
    
    return HttpResponse("Error: No se proporcionó ningún archivo HTML", status=400)
  