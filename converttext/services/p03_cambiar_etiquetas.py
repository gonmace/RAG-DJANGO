import re

def cambiar_etiquetas(texto, palabras_clave, etiqueta_original, etiqueta_nueva):
    """
    Cambia las etiquetas HTML de las líneas que comienzan con palabras clave específicas.
    
    Args:
        texto (str): Texto HTML a procesar
        palabras_clave (list): Lista de palabras que indican qué líneas modificar
        etiqueta_original (str): Etiqueta HTML original a buscar (ej: 'h3')
        etiqueta_nueva (str): Nueva etiqueta HTML a usar (ej: 'p')
        
    Returns:
        str: Texto con las etiquetas modificadas
    """
    # Dividir el texto en líneas y limpiar espacios
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
    resultado = []
    
    for linea in lineas:
        # Extraer el texto sin etiquetas HTML
        texto_limpio = re.sub(r'<[^>]+>', '', linea)
        
        # Verificar si la línea comienza con una palabra clave
        es_candidato = False
        for palabra in palabras_clave:
            if texto_limpio.upper().startswith(palabra):
                es_candidato = True
                break
        
        if es_candidato:
            # Buscar y reemplazar la etiqueta original por la nueva
            linea_modificada = re.sub(
                f'<{etiqueta_original}>(.*?)</{etiqueta_original}>',
                f'<{etiqueta_nueva}>\\1</{etiqueta_nueva}>',
                linea
            )
            resultado.append(linea_modificada)
        else:
            resultado.append(linea)
    
    return '\n'.join(resultado)

def procesar_archivo_html(archivo_entrada, archivo_salida, palabras_clave, etiqueta_original, etiqueta_nueva):
    """
    Procesa un archivo HTML para cambiar etiquetas específicas.
    
    Args:
        archivo_entrada (str): Ruta del archivo HTML de entrada
        archivo_salida (str): Ruta del archivo HTML de salida
        palabras_clave (list): Lista de palabras que indican qué líneas modificar
        etiqueta_original (str): Etiqueta HTML original a buscar
        etiqueta_nueva (str): Nueva etiqueta HTML a usar
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
        contenido_procesado = cambiar_etiquetas(body, palabras_clave, etiqueta_original, etiqueta_nueva)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(header + '\n' + contenido_procesado + '\n' + footer)
            
        print(f"Procesamiento completado. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    # Configuración
    archivo_entrada = "salida_con_titulos.html"
    archivo_salida = "salida_con_etiquetas_cambiadas.html"
    palabras_clave = ['ARTÍCULO', 'ARTICULO']
    etiqueta_original = 'h3'
    etiqueta_nueva = 'p'
    
    # Procesar el archivo
    procesar_archivo_html(archivo_entrada, archivo_salida, palabras_clave, etiqueta_original, etiqueta_nueva) 