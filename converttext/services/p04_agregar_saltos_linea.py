import re

def agregar_saltos_linea(texto, palabras_clave):
    """
    Agrega un salto de línea (br) antes de las líneas que contengan palabras clave específicas.
    
    Args:
        texto (str): Texto HTML a procesar
        palabras_clave (list): Lista de palabras que indican dónde agregar saltos de línea
        
    Returns:
        str: Texto con los saltos de línea agregados
    """
    # Dividir el texto en líneas y limpiar espacios
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
    resultado = []
    
    for linea in lineas:
        # Extraer el texto sin etiquetas HTML
        texto_limpio = re.sub(r'<[^>]+>', '', linea)
        
        # Verificar si la línea contiene alguna palabra clave
        necesita_salto = False
        for palabra in palabras_clave:
            if palabra.upper() in texto_limpio.upper():
                necesita_salto = True
                break
        
        if necesita_salto:
            resultado.append('<br>')  # Agregar etiqueta br
        resultado.append(linea)
    
    return '\n'.join(resultado)

def procesar_archivo_html(archivo_entrada, archivo_salida, palabras_clave):
    """
    Procesa un archivo HTML para agregar saltos de línea antes de líneas específicas.
    
    Args:
        archivo_entrada (str): Ruta del archivo HTML de entrada
        archivo_salida (str): Ruta del archivo HTML de salida
        palabras_clave (list): Lista de palabras que indican dónde agregar saltos de línea
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
        contenido_procesado = agregar_saltos_linea(body, palabras_clave)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(header + '\n' + contenido_procesado + '\n' + footer)
            
        print(f"Procesamiento completado. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    # Configuración
    archivo_entrada = "salida_con_etiquetas_cambiadas.html"
    archivo_salida = "salida_con_saltos_linea.html"
    palabras_clave = ['ARTÍCULO', 'ARTICULO']
    
    # Procesar el archivo
    procesar_archivo_html(archivo_entrada, archivo_salida, palabras_clave) 