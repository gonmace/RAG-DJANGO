"""
Este archivo hace que el directorio services sea un paquete Python y exporta las funciones
con los nombres originales que incluyen prefijos numéricos.
"""

from .p00_pdf_to_html import pdf_a_html
from .p01_eliminar_lineas import procesar_archivo_html as eliminar_lineas
from .p02_titles import procesar_archivo_html as procesar_titulos
from .p03_cambiar_etiquetas import procesar_archivo_html as cambiar_etiquetas
from .p04_agregar_saltos_linea import agregar_saltos_linea, procesar_archivo_html as procesar_saltos_linea
from .p05_agrupar_parrafos import procesar_archivo_html as agrupar_parrafos
from .p06_html_to_md import procesar_archivo as html_a_markdown
from .p07_eliminar_duplicados import procesar_archivo as eliminar_duplicados

__all__ = [
    'pdf_a_html',
    'eliminar_lineas',
    'procesar_titulos',
    'cambiar_etiquetas',
    'agregar_saltos_linea',
    'procesar_saltos_linea',
    'agrupar_parrafos',
    'html_a_markdown',
    'eliminar_duplicados'
]
