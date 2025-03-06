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
                
                # Inicializar variables
                libro = ""
                titulo = ""
                capitulo = ""
                ultimo_capitulo = ""  # Nueva variable para mantener el último capítulo
                
                # Almacenar los metadatos
                chunks_with_metadata = []
                
                # Inicializar variables para el procesamiento
                parts = []
                current_part = ""
                
                # Procesar el texto línea por línea
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    # Si la línea está vacía, tambien la agregamos al fragmento actual
                    if not line.strip():
                        current_part += '\n' + line
                        continue
                        
                    # Si la línea comienza con #### y no con ######, hacemos una nueva división
                    if line.startswith('####') and not line.startswith('#####'):
                        # Verificar si la siguiente línea no vacía comienza con #####
                        next_line = None
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip():  # Encontrar la siguiente línea no vacía
                                next_line = lines[j]
                                if next_line.startswith('#####') and not next_line.startswith('######'):
                                    # Si encontramos una línea con #####, no hacemos nada aquí
                                    # y esperamos a que se procese esa línea
                                    current_part += '\n'
                                    break
                                break
                        
                        # Si no encontramos una línea con #####, hacemos la división aquí
                        if not next_line or not (next_line.startswith('#####') and not next_line.startswith('######')):
                            if current_part:
                                parts.append(current_part)
                            current_part = line
                        continue
                    
                    # Si la línea comienza con ##### y no con ######, hacemos una nueva división
                    if line.startswith('#####') and not line.startswith('######'):
                        if current_part:
                            parts.append(current_part)
                        current_part = line
                        continue
                    
                    # Para cualquier otra línea, la añadimos al fragmento actual
                    current_part += '\n' + line if current_part else line

                # Añadir la última parte si existe
                if current_part:
                    parts.append(current_part)



                ppp=0
                # Procesar cada fragmento
                for part in parts:
                    if not part.strip():
                        continue
                    # Buscar títulos
                    capitulo_match = re.search(r'^####\s*([^#].*?)(?:\n|$)', part)
                    seccion_match = re.search(r'^#####\s*([^#].*?)(?:\n|$)', part)
                    # Si no hay ningún título válido, saltar
                    if not capitulo_match and not seccion_match:
                        continue
                    
                    # Obtener el contenido después del primer título
                    lines = part.split('\n')
                    chunk_lines = []
                    for line in lines[1:]:  # Saltamos la primera línea que es el título
                        if not line.startswith('###') and not line.startswith('##'):  # Excluimos las líneas que son títulos
                            chunk_lines.append(line)
                    chunk = '\n'.join(chunk_lines).strip()
                    
                    # Asignar capítulo y sección
                    if capitulo_match and seccion_match:
                        # Si tenemos ambos títulos, usamos el de 4 almohadillas como capítulo
                        capitulo = capitulo_match.group(1).strip()
                        ultimo_capitulo = capitulo  # Actualizamos el último capítulo
                        seccion = seccion_match.group(1).strip()
                    elif capitulo_match:
                        # Si solo tenemos título de 4 almohadillas
                        capitulo = capitulo_match.group(1).strip()
                        ultimo_capitulo = capitulo  # Actualizamos el último capítulo
                        seccion = "_"
                    elif seccion_match:
                        # Si solo tenemos título de 5 almohadillas, usamos el último capítulo
                        capitulo = ultimo_capitulo
                        seccion = seccion_match.group(1).strip()
                    
                    # Buscar el libro y título correspondientes
                    prev_text = text[:text.find(part)]

                    libro_match = re.findall(r'^##\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    ultimo_libro = libro_match[-1] if libro_match else "Sin libro"
            
                    titulo_match = re.findall(r'^###\s*([^#].*?)(?:\n|$)', prev_text, re.MULTILINE)
                    ultimo_titulo = titulo_match[-1] if titulo_match else "Sin título"
                    
                    chunks_with_metadata.append({
                        'libro': ultimo_libro,
                        'titulo': ultimo_titulo,
                        'capitulo': capitulo,
                        'seccion': seccion,
                        'text': chunk
                    })
                
                return render(request, 'splitters/splitters.html', {
                    'chunks': chunks_with_metadata
                })
            else:
                messages.error(request, 'Por favor, sube un archivo Markdown (.md)')
        else:
            messages.error(request, 'Por favor, sube un archivo')
            
    return render(request, 'splitters/splitters.html')


