from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmbeddingForm
from .services import LangChainService
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


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
