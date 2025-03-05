def eliminar_lineas_duplicadas(texto, min_chars=100):
    """
    Elimina líneas duplicadas en todo el texto, manteniendo el orden original
    de la primera aparición de cada línea. Solo analiza líneas con más de 100 caracteres.
    
    Args:
        texto (str): Texto Markdown a procesar
        min_chars (int): Número mínimo de caracteres para analizar duplicados (por defecto 100)
        
    Returns:
        str: Texto con las líneas duplicadas eliminadas
    """
    # Dividir el texto en líneas
    lineas = texto.split('\n')
    # Usar un conjunto para rastrear líneas únicas
    lineas_vistas = set()
    # Lista para mantener el orden original
    resultado = []
    
    for linea in lineas:
        # Solo analizar líneas con más de 100 caracteres
        if len(linea) > min_chars:
            # Solo agregar la línea si no la hemos visto antes
            if linea not in lineas_vistas:
                resultado.append(linea)
                lineas_vistas.add(linea)
        else:
            # Si la línea tiene 100 caracteres o menos, siempre se mantiene
            resultado.append(linea)
    
    return '\n'.join(resultado)

def procesar_archivo(archivo_entrada, archivo_salida, min_chars=100):
    """
    Procesa un archivo Markdown para eliminar líneas duplicadas.
    
    Args:
        archivo_entrada (str): Ruta del archivo Markdown de entrada
        archivo_salida (str): Ruta del archivo Markdown de salida
        min_chars (int): Número mínimo de caracteres para analizar duplicados (por defecto 100)
    """
    try:
        # Leer el archivo Markdown
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Procesar el contenido
        contenido_procesado = eliminar_lineas_duplicadas(contenido, min_chars)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(contenido_procesado)
            
        print(f"Procesamiento completado. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    # Configuración
    archivo_entrada = "documento.md"
    archivo_salida = "documento_sin_duplicados.md"
    min_chars = 100
    
    # Procesar el archivo
    procesar_archivo(archivo_entrada, archivo_salida, min_chars) 