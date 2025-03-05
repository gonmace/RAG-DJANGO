"""
Este archivo hace que el directorio services sea un paquete Python y exporta las funciones
con los nombres originales que incluyen prefijos numéricos.
"""

from .p01_pdf_to_html import pdf_a_html
from .p02_titles import procesar_archivo_html as procesar_titulos
from .p03_cambiar_etiquetas import procesar_archivo_html
from .p04_agregar_saltos_linea import agregar_saltos_linea
from .p05_agrupar_parrafos import agrupar_parrafos
from .p06_html_to_md import procesar_archivo as html_a_markdown

__all__ = [
    'pdf_a_html',
    'procesar_titulos',
    'procesar_archivo_html',
    'agregar_saltos_linea',
    'agrupar_parrafos',
    'html_a_markdown'
]
