from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmbeddingForm
from .services import LangChainService
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
import re
from langchain.text_splitter import MarkdownTextSplitter
import tiktoken
import uuid


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


@require_http_methods(["GET"])
def create_embeddings_MDtitles(request):
    try:
        # Obtener los chunks de la sesión
        chunks_data = request.session.get('chunks_with_metadata', [])
        
        if not chunks_data:
            return StreamingHttpResponse(
                f"data: {json.dumps({'error': 'No hay fragmentos para procesar. Por favor, primero divide el documento.'})}\n\n",
                content_type='text/event-stream'
            )
        
        # Obtener y validar el rango
        rango = request.GET.get('rango', '')
        if rango:
            try:
                inicio, fin = map(int, rango.split('-'))
                if inicio < 1 or fin > len(chunks_data) or inicio > fin:
                    return StreamingHttpResponse(
                        f"data: {json.dumps({'error': 'Rango inválido. Por favor verifica los valores.'})}\n\n",
                        content_type='text/event-stream'
                    )
                # Ajustar el rango para índices base-0
                chunks_data = chunks_data[inicio-1:fin]
            except ValueError:
                return StreamingHttpResponse(
                    f"data: {json.dumps({'error': 'Formato de rango inválido. Use el formato inicio-fin (ejemplo: 1-10)'})}\n\n",
                    content_type='text/event-stream'
                )
        
        # Obtener la preferencia de incluir títulos
        incluir_titulos = request.session.get('incluir_titulos', False)
        
        def generate_progress():
            service = LangChainService()
            embeddings_created = 0
            total_chunks = len(chunks_data)
            
            try:
                # Obtener los nombres personalizados de los títulos de la sesión
                titulo1_nombre = request.session.get('titulo1_nombre', 'Documento')
                titulo2_nombre = request.session.get('titulo2_nombre', 'Libro')
                titulo3_nombre = request.session.get('titulo3_nombre', 'Título')
                titulo4_nombre = request.session.get('titulo4_nombre', 'Capítulo')
                titulo5_nombre = request.session.get('titulo5_nombre', 'Sección')
                titulo6_nombre = request.session.get('titulo6_nombre', 'Subsección')
                
                # Mapeo de títulos a nombres personalizados
                titulo_mapping = {
                    'titulo1': titulo1_nombre,
                    'titulo2': titulo2_nombre,
                    'titulo3': titulo3_nombre,
                    'titulo4': titulo4_nombre,
                    'titulo5': titulo5_nombre,
                    'titulo6': titulo6_nombre
                }
                
                # Enviar mensaje inicial
                yield f"data: {json.dumps({'status': 'Iniciando creación de embeddings...', 'progress': 0, 'current': 0, 'total': total_chunks})}\n\n"
                
                # Procesar cada fragmento
                for i, chunk in enumerate(chunks_data, 1):
                    if incluir_titulos:
                        # Crear el texto completo con títulos y contenido
                        texto_completo = []
                        for j in range(1, 7):
                            titulo_key = f'titulo{j}'
                            if titulo_key in chunk:
                                texto_completo.append(chunk[titulo_key])
                        
                        # Agregar el contenido después de los títulos
                        texto_completo.append(chunk['text'])
                        
                        # Unir todo el texto con dobles saltos de línea
                        texto_final = '\n\n'.join(texto_completo)
                    else:
                        # Usar solo el texto del chunk sin los títulos
                        texto_final = chunk['text']
                    
                    # Crear metadatos con nombres personalizados
                    metadatos = {'id': str(uuid.uuid4())}  # Agregar ID único
                    
                    # Encontrar el último título y los títulos previos
                    for j in range(1, 7):
                        titulo_key = f'titulo{j}'
                        if titulo_key in chunk:
                            nombre_personalizado = titulo_mapping[titulo_key]
                            metadatos[nombre_personalizado] = chunk[titulo_key]
                    
                    # Enviar actualización de progreso
                    porcentaje = (i / total_chunks) * 100
                    yield f"data: {json.dumps({'status': f'Procesando fragmento {i}/{total_chunks}', 'progress': porcentaje, 'current': i, 'total': total_chunks})}\n\n"
                    
                    # Añadir el documento
                    service.add_document(texto_final, metadatos)
                    embeddings_created += 1
                
                # Limpiar los chunks de la sesión solo si todo fue exitoso
                del request.session['chunks_with_metadata']
                request.session.modified = True
                
                # Enviar mensaje de éxito
                yield f"data: {json.dumps({'success': True, 'message': f'Se crearon {embeddings_created} embeddings exitosamente'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Error al crear embeddings: {str(e)}'})}\n\n"
        
        return StreamingHttpResponse(
            generate_progress(),
            content_type='text/event-stream'
        )
            
    except Exception as e:
        return StreamingHttpResponse(
            f"data: {json.dumps({'error': f'Error inesperado: {str(e)}'})}\n\n",
            content_type='text/event-stream'
        )

@require_http_methods(["GET"])
def create_embeddings_MDsubdivide(request):
    try:
        # Obtener los chunks de la sesión
        chunks_data = request.session.get('chunks_with_metadata', [])
        
        if not chunks_data:
            return StreamingHttpResponse(
                f"data: {json.dumps({'error': 'No hay fragmentos para procesar. Por favor, primero divide el documento.'})}\n\n",
                content_type='text/event-stream'
            )

        # Obtener el rango de fragmentos
        rango_fragmentos = request.GET.get('rango', f'1-{len(chunks_data)}')
        try:
            inicio, fin = map(int, rango_fragmentos.split('-'))
            # Ajustar índices a base 0 y validar rangos
            inicio = max(1, min(inicio, len(chunks_data))) - 1
            fin = max(1, min(fin, len(chunks_data))) - 1
            if inicio > fin:
                inicio, fin = fin, inicio
            chunks_data = chunks_data[inicio:fin + 1]
        except ValueError:
            return StreamingHttpResponse(
                f"data: {json.dumps({'error': 'Formato de rango inválido. Use el formato: inicio-fin (ejemplo: 1-10)'})}\n\n",
                content_type='text/event-stream'
            )
        
        def generate_progress():
            service = LangChainService()
            embeddings_created = 0
            total_chunks = len(chunks_data)
            
            try:
                # Enviar mensaje inicial
                yield f"data: {json.dumps({'status': 'Iniciando creación de embeddings...', 'progress': 0, 'current': 0, 'total': total_chunks})}\n\n"
                
                # Procesar cada fragmento
                for i, chunk in enumerate(chunks_data, 1):

                    # Obtener el texto del chunk
                    texto = chunk.get('text', '')
                    
                    # Crear metadatos con Documento y ID_Original
                    metadatos = {
                        'Documento': chunk.get('metadata', {}).get('Documento', ''),
                        'ID_Original': chunk.get('metadata', {}).get('ID_Original', '') 
                    }
                    
                    # Enviar actualización de progreso
                    porcentaje = (i / total_chunks) * 100
                    yield f"data: {json.dumps({'status': f'Procesando fragmento {i}/{total_chunks}', 'progress': porcentaje, 'current': i, 'total': total_chunks})}\n\n"
                    
                    # Añadir el documento
                    service.add_document(texto, metadatos)
                    embeddings_created += 1
                
                # Limpiar los chunks de la sesión solo si todo fue exitoso
                del request.session['chunks_with_metadata']
                request.session.modified = True
                
                # Enviar mensaje de éxito
                yield f"data: {json.dumps({'success': True, 'message': f'Se crearon {embeddings_created} embeddings exitosamente'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Error al crear embeddings: {str(e)}'})}\n\n"
        
        return StreamingHttpResponse(
            generate_progress(),
            content_type='text/event-stream'
        )
            
    except Exception as e:
        return StreamingHttpResponse(
            f"data: {json.dumps({'error': f'Error inesperado: {str(e)}'})}\n\n",
            content_type='text/event-stream'
        )

def split_documents_view(request):
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            if file.name.endswith('.md'):
                text = file.read().decode('utf-8')
                
                # Inicializar el codificador de tiktoken
                enc = tiktoken.get_encoding("cl100k_base")
                
                # Obtener los nombres personalizados de los títulos
                titulo1_nombre = request.POST.get('titulo1_nombre', 'Documento')
                titulo2_nombre = request.POST.get('titulo2_nombre', 'Libro')
                titulo3_nombre = request.POST.get('titulo3_nombre', 'Título')
                titulo4_nombre = request.POST.get('titulo4_nombre', 'Capítulo')
                titulo5_nombre = request.POST.get('titulo5_nombre', 'Sección')
                titulo6_nombre = request.POST.get('titulo6_nombre', 'Subsección')
                
                # Guardar los nombres personalizados y la preferencia de incluir títulos en la sesión
                request.session['titulo1_nombre'] = titulo1_nombre
                request.session['titulo2_nombre'] = titulo2_nombre
                request.session['titulo3_nombre'] = titulo3_nombre
                request.session['titulo4_nombre'] = titulo4_nombre
                request.session['titulo5_nombre'] = titulo5_nombre
                request.session['titulo6_nombre'] = titulo6_nombre
                request.session['incluir_titulos'] = 'incluir_titulos' in request.POST
                request.session.modified = True
                
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
                        
                        # Asegurarnos de que el nivel esté entre 1 y 6
                        if 1 <= nivel <= 6 and nivel in niveles_seleccionados:
                            # Si el nivel está seleccionado, crear un nuevo fragmento
                            if current_part:
                                parts.append(current_part)
                            current_part = line
                        else:
                            # Si el nivel no está seleccionado o es inválido, mantener el título sin #
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
                    current_level = None
                    current_match = None
                    
                    # Verificar cada nivel en orden
                    if titulo1_match and 1 in niveles_seleccionados:
                        current_level = 1
                        current_match = titulo1_match
                    elif titulo2_match and 2 in niveles_seleccionados:
                        current_level = 2
                        current_match = titulo2_match
                    elif titulo3_match and 3 in niveles_seleccionados:
                        current_level = 3
                        current_match = titulo3_match
                    elif titulo4_match and 4 in niveles_seleccionados:
                        current_level = 4
                        current_match = titulo4_match
                    elif titulo5_match and 5 in niveles_seleccionados:
                        current_level = 5
                        current_match = titulo5_match
                    elif titulo6_match and 6 in niveles_seleccionados:
                        current_level = 6
                        current_match = titulo6_match
                    
                    if current_level is not None:
                        # Añadir títulos previos según el nivel actual
                        if current_level >= 1 and ultimo_titulo1 and 1 in niveles_seleccionados:
                            metadata['titulo1'] = ultimo_titulo1
                        if current_level >= 2 and ultimo_titulo2 and 2 in niveles_seleccionados:
                            metadata['titulo2'] = ultimo_titulo2
                        if current_level >= 3 and ultimo_titulo3 and 3 in niveles_seleccionados:
                            metadata['titulo3'] = ultimo_titulo3
                        if current_level >= 4 and ultimo_titulo4 and 4 in niveles_seleccionados:
                            metadata['titulo4'] = ultimo_titulo4
                        if current_level >= 5 and ultimo_titulo5 and 5 in niveles_seleccionados:
                            metadata['titulo5'] = ultimo_titulo5
                        
                        # Añadir el título actual
                        metadata[f'titulo{current_level}'] = current_match.group(1).strip()
                    else:
                        continue
                    
                    # Añadir el texto al diccionario de metadatos
                    metadata['text'] = chunk
                    # Calcular tokens del fragmento
                    if 'incluir_titulos' in request.POST:
                        # Si se incluyen títulos, calcular tokens del texto completo
                        fragment_text = ""
                        for j in range(1, 7):
                            titulo_key = f'titulo{j}'
                            if titulo_key in metadata:
                                fragment_text += metadata[titulo_key] + "\n"
                        fragment_text += chunk
                        metadata['token_count'] = len(enc.encode(fragment_text))
                    else:
                        # Si no se incluyen títulos, calcular solo tokens del texto
                        metadata['token_count'] = len(enc.encode(chunk))
                    chunks_with_metadata.append(metadata)
                
                # Calcular máximo y mínimo de tokens
                token_counts = [chunk['token_count'] for chunk in chunks_with_metadata]
                max_tokens = max(token_counts) if token_counts else 0
                min_tokens = min(token_counts) if token_counts else 0
                total_tokens = sum(token_counts) if token_counts else 0
                
                # Calcular precio en USD (0.02 USD por millón de tokens)
                price_usd = (total_tokens / 1_000_000) * 0.02
                
                # Convertir los chunks a un formato serializable
                serializable_chunks = []
                for chunk in chunks_with_metadata:
                    serializable_chunk = {
                        'text': chunk['text'],
                        'token_count': chunk['token_count']
                    }
                    # Añadir títulos si existen
                    for i in range(1, 7):
                        titulo_key = f'titulo{i}'
                        if titulo_key in chunk:
                            serializable_chunk[titulo_key] = chunk[titulo_key]
                    serializable_chunks.append(serializable_chunk)
                
                # Guardar los chunks en la sesión
                request.session['chunks_with_metadata'] = serializable_chunks
                request.session.modified = True
                
                return render(request, 'splitters/MDtitles.html', {
                    'chunks': chunks_with_metadata,
                    'titulo1_nombre': titulo1_nombre,
                    'titulo2_nombre': titulo2_nombre,
                    'titulo3_nombre': titulo3_nombre,
                    'titulo4_nombre': titulo4_nombre,
                    'titulo5_nombre': titulo5_nombre,
                    'titulo6_nombre': titulo6_nombre,
                    'max_tokens': max_tokens,
                    'min_tokens': min_tokens,
                    'total_tokens': total_tokens,
                    'price_usd': price_usd
                })
            else:
                messages.error(request, 'Por favor, sube un archivo Markdown (.md)')
        else:
            messages.error(request, 'Por favor, sube un archivo')
            
    return render(request, 'splitters/MDtitles.html')


def similaridad_view(request):
    service = LangChainService()
    documentos = service.get_unique_document_values()
    resultado = None
    texto_consulta = None
    documento_seleccionado = None
    umbral = None
    filtro_metadatos = None
    filtro_adicional = None
    filtro_metadatos_raw = ""  # Inicializar la variable con un valor por defecto

    if request.method == 'POST':
        texto_consulta = request.POST.get('texto_consulta')
        documento_seleccionado = request.POST.get('documento_seleccionado')
        num_resultados = int(request.POST.get('num_resultados', 5))
        umbral = float(request.POST.get('umbral', 0))
        filtro_metadatos_raw = request.POST.get('filtro_metadatos', '')

        # Preparar el filtro
        filtro = {}
        
        # Agregar filtro por documento si se seleccionó uno
        if documento_seleccionado:
            filtro['Documento'] = documento_seleccionado

        # Procesar filtro adicional de metadatos si se proporcionó
        if filtro_metadatos_raw.strip():
            try:
                filtro_metadatos_raw_fixed = filtro_metadatos_raw.strip().replace("'", '"')
                filtro_adicional = json.loads(filtro_metadatos_raw_fixed)
            except json.JSONDecodeError:
                messages.error(request, 'El formato del filtro de metadatos debe ser JSON válido.')
                return render(request, 'embeddings/similaridad.html', {
                    'documentos': documentos,
                    'texto_consulta': texto_consulta,
                    'documento_seleccionado': documento_seleccionado,
                    'umbral': umbral,
                    'filtro_metadatos': filtro_metadatos_raw
                })

        try:
            # Realizar la búsqueda con el filtro combinado
            resultados = service.similarity_search(
                query=texto_consulta,
                k=num_resultados,
                filter=filtro_adicional if filtro_adicional else filtro
            )

            # Filtrar por umbral si se especificó
            if umbral > 0:
                resultado = [(doc, score) for doc, score in resultados if score >= umbral]
            else:
                resultado = resultados

        except Exception as e:
            messages.error(request, f'Error al realizar la búsqueda: {str(e)}')

    return render(request, 'embeddings/similaridad.html', {
        'documentos': documentos,
        'resultado': resultado,
        'texto_consulta': texto_consulta,
        'documento_seleccionado': documento_seleccionado,
        'umbral': umbral,
        'filtro_metadatos': filtro_metadatos_raw
    })


def subdivide_documents_view(request):
    # Obtener los documentos únicos de la base de datos
    service = LangChainService()
    documentos = []
    try:
        # Obtener valores únicos del metadato 'Documento'
        documentos = service.get_unique_document_values()
    except Exception as e:
        messages.error(request, f'Error al obtener los documentos: {str(e)}')

    if request.method == 'POST':
        documento_seleccionado = request.POST.get('documento_seleccionado', '')
        keyword = request.POST.get('keyword', '').strip()
        keep_metadata = 'keep_metadata' in request.POST

        if not documento_seleccionado:
            messages.error(request, 'Por favor, selecciona un documento')
            return render(request, 'splitters/MDsubdivide.html', {'documentos': documentos})

        if not keyword:
            messages.error(request, 'Por favor, ingresa una palabra clave')
            return render(request, 'splitters/MDsubdivide.html', {'documentos': documentos})

        try:
            # Obtener los chunks subdivididos
            chunks = service.subdivide_by_keyword(documento_seleccionado, keyword)
            
            if not chunks:
                messages.warning(request, f'No se encontraron párrafos que contengan la palabra "{keyword}"')
                return render(request, 'splitters/MDsubdivide.html', {
                    'documentos': documentos,
                    'documento_seleccionado': documento_seleccionado
                })

            # Guardar los chunks en la sesión
            request.session['chunks_with_metadata'] = chunks
            request.session.modified = True

            return render(request, 'splitters/MDsubdivide.html', {
                'documentos': documentos,
                'documento_seleccionado': documento_seleccionado,
                'chunks': chunks
            })

        except Exception as e:
            messages.error(request, f'Error al subdividir el documento: {str(e)}')
    
    return render(request, 'splitters/MDsubdivide.html', {
        'documentos': documentos
    })


