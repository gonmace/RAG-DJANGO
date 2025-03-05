import re

def eliminar_lineas(texto, texto_a_eliminar):
    """
    Elimina las líneas que contengan el texto especificado.
    
    Args:
        texto (str): Texto HTML a procesar
        texto_a_eliminar (str): Texto que se debe buscar para eliminar las líneas que lo contengan
        
    Returns:
        str: Texto con las líneas eliminadas
    """
    # Dividir el texto en líneas y limpiar espacios
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
    resultado = []
    
    for linea in lineas:
        # Extraer el texto sin etiquetas HTML
        texto_limpio = re.sub(r'<[^>]+>', '', linea)
        
        # Solo mantener las líneas que NO contengan el texto a eliminar
        if texto_a_eliminar.upper() not in texto_limpio.upper():
            resultado.append(linea)
    
    return '\n'.join(resultado)

def procesar_archivo_html(archivo_entrada, archivo_salida, texto_a_eliminar):
    """
    Procesa un archivo HTML para eliminar líneas que contengan un texto específico.
    
    Args:
        archivo_entrada (str): Ruta del archivo HTML de entrada
        archivo_salida (str): Ruta del archivo HTML de salida
        texto_a_eliminar (str): Texto que se debe buscar para eliminar las líneas que lo contengan
    """
    try:
        # Leer el archivo HTML
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Separar el encabezado y el pie del HTML
        partes = contenido.split('<body>')
        if len(partes) != 2:
            raise ValueError("El archivo HTML no tiene la estructura esperada")
            
        header = partes[0] + '<body>'
        body = partes[1].split('</body>')[0]
        footer = '</body>' + partes[1].split('</body>')[1]
        
        # Procesar el contenido del body
        contenido_procesado = eliminar_lineas(body, texto_a_eliminar)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(header + '\n' + contenido_procesado + '\n' + footer)
            
        print(f"Procesamiento completado. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    # Configuración
    archivo_entrada = "salida.html"
    archivo_salida = "salida_sin_lineas.html"
    texto_a_eliminar = "texto a eliminar"
    
    # Procesar el archivo
    procesar_archivo_html(archivo_entrada, archivo_salida, texto_a_eliminar) 