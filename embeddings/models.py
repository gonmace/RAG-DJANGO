from django.db import models

# Create your models here.

class Embedding(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    archivo = models.FileField(upload_to='embeddings/', verbose_name="Archivo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    procesado = models.BooleanField(default=False, verbose_name="Procesado")

    class Meta:
        verbose_name = "Embedding"
        verbose_name_plural = "Embeddings"

    def __str__(self):
        return self.nombre
