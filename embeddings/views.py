from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmbeddingForm
from .services import LangChainService
import json

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

def crear_embedding(request):
    if request.method == 'POST':
        form = EmbeddingForm(request.POST)
        if form.is_valid():
            texto = form.cleaned_data['texto']
            try:
                metadatos = json.loads(form.cleaned_data['metadatos'])
            except json.JSONDecodeError:
                messages.error(request, 'El formato de los metadatos debe ser JSON válido.')
                return render(request, 'embeddings/crear.html', {'form': form})

            # Usar el servicio LangChain para procesar el texto

            service = LangChainService()
            try:
                service.add_texts([texto], [metadatos])
                messages.success(request, 'Embedding creado exitosamente.')
                return redirect('embeddings:listar')
            except Exception as e:
                messages.error(request, f'Error al crear el embedding: {str(e)}')
    else:
        form = EmbeddingForm()
    
    return render(request, 'embeddings/crear.html', {'form': form})
