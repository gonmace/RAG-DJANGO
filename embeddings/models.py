from django.db import models
from main.models import Proyecto
# Create your models here.

# class Parrafo(models.Model):
#     texto = models.TextField(verbose_name="Texto")
#     metadatos = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")
#     proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="parrafos")


#     class Meta:
#         verbose_name = "Párrafo"
#         verbose_name_plural = "Párrafos"

#     def __str__(self):
#         return self.metadatos
