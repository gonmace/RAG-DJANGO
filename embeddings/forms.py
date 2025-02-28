from django import forms
from .models import Embedding

class EmbeddingForm(forms.ModelForm):
    class Meta:
        model = Embedding
        fields = ['nombre', 'archivo']
        # widgets = {
        #     'nombre': forms.TextInput(attrs={
        #         'class': 'input input-bordered w-full',
        #         'placeholder': 'Nombre del embedding'
        #     }),
        #     'archivo': forms.FileInput(attrs={
        #         'class': 'file-input file-input-bordered w-full',
        #     })
        # } 