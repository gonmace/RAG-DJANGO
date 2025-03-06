from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmbeddingForm
from .services import LangChainService
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import re
from langchain.text_splitter import MarkdownTextSplitter


# Create your views here.
def listar_embeddings(request):
    service = LangChainService()
    try:
        documents = service.get_all_documents()

        return render(request, 'embeddings/listar.html', {
            'documents': documents,
            'error': None
        })
    except Exception as e:
        return render(request, 'embeddings/listar.html', {
            'documents': [],
            'error': f'Error al obtener los embeddings: {str(e)}'
        })


def add_document(request):
    if request.method == 'POST':
        form = EmbeddingForm(request.POST)
        if form.is_valid():
            texto = form.cleaned_data['texto']
            metadatos_raw = form.cleaned_data['metadatos']

            try:
                # Si los metadatos están vacíos, usar un diccionario vacío
                metadatos = json.loads(metadatos_raw) if metadatos_raw.strip() else {}
            except json.JSONDecodeError:
                messages.error(request, 'El formato de los metadatos debe ser JSON válido.')
                return render(request, 'embeddings/crear.html', {'form': form})
            # Usar el servicio LangChain para procesar el texto
            service = LangChainService()
            try:
                service.add_document(texto, metadatos)
                messages.success(request, 'Embedding creado exitosamente.')
                return redirect('embeddings:listar')
            except Exception as e:
                messages.error(request, f'Error al crear el embedding: {str(e)}')
    else:
        form = EmbeddingForm()

    return render(request, 'embeddings/crear.html', {'form': form})


def eliminar_embeddings(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids')
        try:
            if ids:
                service = LangChainService()
                service.delete_documents(ids)
                return JsonResponse({'success': True, 'message': 'Embeddings eliminados exitosamente'})
            return JsonResponse({'success': False, 'message': 'No se seleccionaron embeddings para eliminar'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@require_http_methods(["POST"])
def actualizar_embedding(request):
    try:
        data = json.loads(request.body)
        doc_id = data.get('id')
        new_text = data.get('text')
        new_metadata_raw = data.get('metadata')

        if not all([doc_id, new_text]):
            return JsonResponse({
                'success': False,
                'message': 'Se requieren ID y texto'
            }, status=400)

        # Manejo de metadatos
        if new_metadata_raw is None or (isinstance(new_metadata_raw, str) and not new_metadata_raw.strip()):
            new_metadata = {}
        else:
            try:
                if isinstance(new_metadata_raw, str):
                    new_metadata = json.loads(new_metadata_raw)
                else:
                    new_metadata = new_metadata_raw

                if not isinstance(new_metadata, dict):
                    return JsonResponse({
                        'success': False,
                        'message': 'Los metadatos deben ser un objeto JSON válido'
                    }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'El formato de los metadatos debe ser JSON válido. Ejemplo: {"fuente": "libro", "autor": "Juan"}'
                }, status=400)

        service = LangChainService()
        service.update_text(doc_id, new_text, new_metadata)

        return JsonResponse({
            'success': True,
            'message': 'Embedding actualizado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def split_documents_view(request):
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            if file.name.endswith('.md'):
                text = file.read().decode('utf-8')
                
                # Obtener los nombres personalizados de los títulos
                titulo1_nombre = request.POST.get('titulo1_nombre', 'Documento')
                titulo2_nombre = request.POST.get('titulo2_nombre', 'Libro')
                titulo3_nombre = request.POST.get('titulo3_nombre', 'Título')
                titulo4_nombre = request.POST.get('titulo4_nombre', 'Capítulo')
                titulo5_nombre = request.POST.get('titulo5_nombre', 'Sección')
                titulo6_nombre = request.POST.get('titulo6_nombre', 'Subsección')
                
                # Obtener los niveles seleccionados para fragmentar
                niveles_seleccionados = []
                for i in range(1, 7):
                    if request.POST.get(f'usar_titulo{i}'):
                        niveles_seleccionados.append(i)
                
                # Almacenar los metadatos
                chunks_with_metadata = []
                
                # Inicializar variables para el procesamiento
                parts = []
                current_part = ""
                
                # Procesar el texto línea por línea
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    # Si la línea está vacía, la agregamos al fragmento actual
                    if not line.strip():
                        current_part += '\n' + line
                        continue
                    
                    # Detectar si es un título
                    if line.startswith('#'):
                        # Contar el número de # al inicio
                        nivel = len(re.match(r'^#+', line).group())
                        
                        if nivel in niveles_seleccionados:
                            # Si el nivel está seleccionado, crear un nuevo fragmento
                            if current_part:
                                parts.append(current_part)
                            current_part = line
                        else:
                            # Si el nivel no está seleccionado, mantener el título sin #
                            titulo_sin_almohadillas = re.sub(r'^#+\s*', '', line)
                            current_part += '\n' + titulo_sin_almohadillas if current_part else titulo_sin_almohadillas
                        continue
                    
                    # Para cualquier otra línea, la añadimos al fragmento actual
                    current_part += '\n' + line if current_part else line

                # Añadir la última parte si existe
                if current_part:
                    parts.append(current_part)

                # Procesar cada fragmento
                for part in parts:
                    if not part.strip():
                        continue
                    
                    # Buscar títulos de diferentes niveles
                    titulo1_match = re.search(r'^#\s*([^#].*?)(?:\n|$)', part)
                    titulo2_match = re.search(r'^##\s*([^#].*?)(?:\n|$)', part)
                    titulo3_match = re.search(r'^###\s*([^#].*?)(?:\n|$)', part)
                    titulo4_match = re.search(r'^####\s*([^#].*?)(?:\n|$)', part)
                    titulo5_match = re.search(r'^#####\s*([^#].*?)(?:\n|$)', part)
                    titulo6_match = re.search(r'^######\s*([^#].*?)(?:\n|$)', part)
                    
                    # Obtener el contenido después del título
                    lines = part.split('\n')
                    chunk_lines = []
                    first_line = True
                    for line in lines:
                        if first_line:
                            # La primera línea es el título que inició el fragmento
                            first_line = False
                            continue
                        chunk_lines.append(line)
                    chunk = '\n'.join(chunk_lines).strip()
                    
                    # Si el contenido está vacío después de eliminar espacios, saltamos este fragmento
                    if not chunk:
                        continue
                    
                    # Buscar el texto previo para mantener la jerarquía
                    prev_text = text[:text.find(part)]
                    
                    # Encontrar el último título de cada nivel en el texto previo
                    titulo1_prev = re.findall(r'^#\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    titulo2_prev = re.findall(r'^##\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    titulo3_prev = re.findall(r'^###\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    titulo4_prev = re.findall(r'^####\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    titulo5_prev = re.findall(r'^#####\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    
                    # Obtener los últimos títulos encontrados o usar None
                    ultimo_titulo1 = titulo1_prev[-1] if titulo1_prev else None
                    ultimo_titulo2 = titulo2_prev[-1] if titulo2_prev else None
                    ultimo_titulo3 = titulo3_prev[-1] if titulo3_prev else None
                    ultimo_titulo4 = titulo4_prev[-1] if titulo4_prev else None
                    ultimo_titulo5 = titulo5_prev[-1] if titulo5_prev else None
                    
                    # Inicializar diccionario de metadatos
                    metadata = {}
                    
                    # Determinar el nivel actual y actualizar los metadatos
                    if titulo1_match and 1 in niveles_seleccionados:
                        metadata['titulo1'] = titulo1_match.group(1).strip()
                    elif titulo2_match and 2 in niveles_seleccionados:
                        if ultimo_titulo1 and 1 in niveles_seleccionados:
                            metadata['titulo1'] = ultimo_titulo1
                        metadata['titulo2'] = titulo2_match.group(1).strip()
                    elif titulo3_match and 3 in niveles_seleccionados:
                        if ultimo_titulo1 and 1 in niveles_seleccionados:
                            metadata['titulo1'] = ultimo_titulo1
                        if ultimo_titulo2 and 2 in niveles_seleccionados:
                            metadata['titulo2'] = ultimo_titulo2
                        metadata['titulo3'] = titulo3_match.group(1).strip()
                    elif titulo4_match and 4 in niveles_seleccionados:
                        if ultimo_titulo1 and 1 in niveles_seleccionados:
                            metadata['titulo1'] = ultimo_titulo1
                        if ultimo_titulo2 and 2 in niveles_seleccionados:
                            metadata['titulo2'] = ultimo_titulo2
                        if ultimo_titulo3 and 3 in niveles_seleccionados:
                            metadata['titulo3'] = ultimo_titulo3
                        metadata['titulo4'] = titulo4_match.group(1).strip()
                    elif titulo5_match and 5 in niveles_seleccionados:
                        if ultimo_titulo1 and 1 in niveles_seleccionados:
                            metadata['titulo1'] = ultimo_titulo1
                        if ultimo_titulo2 and 2 in niveles_seleccionados:
                            metadata['titulo2'] = ultimo_titulo2
                        if ultimo_titulo3 and 3 in niveles_seleccionados:
                            metadata['titulo3'] = ultimo_titulo3
                        if ultimo_titulo4 and 4 in niveles_seleccionados:
                            metadata['titulo4'] = ultimo_titulo4
                        metadata['titulo5'] = titulo5_match.group(1).strip()
                    elif titulo6_match and 6 in niveles_seleccionados:
                        if ultimo_titulo1 and 1 in niveles_seleccionados:
                            metadata['titulo1'] = ultimo_titulo1
                        if ultimo_titulo2 and 2 in niveles_seleccionados:
                            metadata['titulo2'] = ultimo_titulo2
                        if ultimo_titulo3 and 3 in niveles_seleccionados:
                            metadata['titulo3'] = ultimo_titulo3
                        if ultimo_titulo4 and 4 in niveles_seleccionados:
                            metadata['titulo4'] = ultimo_titulo4
                        if ultimo_titulo5 and 5 in niveles_seleccionados:
                            metadata['titulo5'] = ultimo_titulo5
                        metadata['titulo6'] = titulo6_match.group(1).strip()
                    else:
                        continue
                    
                    # Añadir el texto al diccionario de metadatos
                    metadata['text'] = chunk
                    chunks_with_metadata.append(metadata)
                
                return render(request, 'splitters/splitters.html', {
                    'chunks': chunks_with_metadata,
                    'titulo1_nombre': titulo1_nombre,
                    'titulo2_nombre': titulo2_nombre,
                    'titulo3_nombre': titulo3_nombre,
                    'titulo4_nombre': titulo4_nombre,
                    'titulo5_nombre': titulo5_nombre,
                    'titulo6_nombre': titulo6_nombre
                })
            else:
                messages.error(request, 'Por favor, sube un archivo Markdown (.md)')
        else:
            messages.error(request, 'Por favor, sube un archivo')
            
    return render(request, 'splitters/splitters.html')


