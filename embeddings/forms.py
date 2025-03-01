from django import forms

class EmbeddingForm(forms.Form):
    texto = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea w-full',
            'placeholder': 'Ingrese el texto aquí',
            'rows': 4
        })
    )
    metadatos = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input w-full',
            'placeholder': 'Metadatos --> {"source": "news"}'
        })
    )
