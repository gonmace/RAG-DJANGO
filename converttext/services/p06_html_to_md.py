import html2text
import re

def normalizar_lineas_vacias(texto):
    """
    Normaliza múltiples líneas vacías a una sola línea.
    
    Args:
        texto (str): Texto a procesar
        
    Returns:
        str: Texto con líneas vacías normalizadas
    """
    # Reemplazar múltiples líneas vacías con una sola
    return re.sub(r'\n\s*\n\s*\n+', '\n\n', texto)

def procesar_archivo(archivo_entrada, archivo_salida):
    """
    Procesa un archivo HTML y lo convierte a Markdown usando html2text.
    
    Args:
        archivo_entrada (str): Ruta del archivo HTML de entrada
        archivo_salida (str): Ruta del archivo Markdown de salida
    """
    try:
        # Configurar el convertidor
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0  # Sin límite de ancho
        h.unicode_snob = True  # Mantener caracteres especiales
        
        # Leer el archivo HTML
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Separar el encabezado y el pie del HTML
        partes = contenido.split('<body>')
        if len(partes) != 2:
            raise ValueError("El archivo HTML no tiene la estructura esperada")
            
        body = partes[1].split('</body>')[0]
        
        # Convertir a Markdown
        contenido_markdown = h.handle(body)
        
        # Normalizar líneas vacías
        contenido_markdown = normalizar_lineas_vacias(contenido_markdown)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(contenido_markdown)
            
        print(f"Conversión completada. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante la conversión: {str(e)}")

if __name__ == "__main__":
    # Configuración
    archivo_entrada = "salida_con_parrafos_agrupados.html"
    archivo_salida = "documento.md"
    
    # Procesar el archivo
    procesar_archivo(archivo_entrada, archivo_salida) 