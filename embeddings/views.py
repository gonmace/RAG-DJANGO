from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmbeddingForm

# Create your views here.
def crear_embedding(request):
    if request.method == 'POST':
        form = EmbeddingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Embedding creado exitosamente.')
            return redirect('embeddings:crear')
    else:
        form = EmbeddingForm()
    
    return render(request, 'embeddings/crear.html', {'form': form})
