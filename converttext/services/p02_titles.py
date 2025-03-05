import re

def identificar_titulos(texto, palabras_titulo, lineas_adicionales, etiqueta='h2'):
    """
    Identifica títulos en el texto basándose en palabras clave y los convierte a la etiqueta especificada.
    Incluye líneas adicionales junto con el título.
    
    Args:
        texto (str): Texto a procesar
        palabras_titulo (list): Lista de palabras que indican títulos
        lineas_adicionales (int): Número de líneas adicionales a incluir con el título
        etiqueta (str): Etiqueta HTML a usar para los títulos (ej: 'h2', 'h3')
        
    Returns:
        str: Texto con los títulos convertidos a la etiqueta especificada
    """
    # Dividir el texto en líneas y limpiar espacios
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
    resultado = []
    i = 0
    
    while i < len(lineas):
        linea = lineas[i]
        
        # Extraer el texto sin etiquetas HTML
        texto_limpio = re.sub(r'<[^>]+>', '', linea)
        
        # Verificar si la línea comienza con una palabra de título
        es_titulo = False
        for palabra in palabras_titulo:
            if texto_limpio.upper().startswith(palabra):
                es_titulo = True
                break
        
        # Si es título, incluir también las líneas adicionales
        if es_titulo:
            # Obtener las líneas adicionales si existen
            lineas_titulo = [texto_limpio]
            for j in range(lineas_adicionales):
                if i + 1 + j < len(lineas):
                    siguiente_linea = re.sub(r'<[^>]+>', '', lineas[i + 1 + j])
                    if siguiente_linea:
                        lineas_titulo.append(siguiente_linea)
            
            # Unir el título y las líneas adicionales con guión
            if len(lineas_titulo) > 1:
                resultado.append(f"<{etiqueta}>{' - '.join(lineas_titulo)}</{etiqueta}>")
                i += 1 + lineas_adicionales  # Avanzar según las líneas procesadas
            else:
                resultado.append(f"<{etiqueta}>{lineas_titulo[0]}</{etiqueta}>")
                i += 1
        else:
            # Si no es título, verificar si es una línea adicional de un título
            if i > 0 and any(re.sub(r'<[^>]+>', '', lineas[i-1]).upper().startswith(palabra) for palabra in palabras_titulo):
                i += 1
                continue
            resultado.append(linea)  # Mantener la línea original con sus etiquetas
            i += 1
    
    return '\n'.join(resultado)

def procesar_archivo_html(archivo_entrada, archivo_salida, palabras_titulo, lineas_adicionales=0, etiqueta='h2'):
    """
    Procesa un archivo HTML para identificar y formatear títulos.
    
    Args:
        archivo_entrada (str): Ruta del archivo HTML de entrada
        archivo_salida (str): Ruta del archivo HTML de salida
        palabras_titulo (list): Lista de palabras que indican títulos
        lineas_adicionales (int): Número de líneas adicionales a incluir con el título
        etiqueta (str): Etiqueta HTML a usar para los títulos (ej: 'h2', 'h3')
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
        contenido_procesado = identificar_titulos(body, palabras_titulo, lineas_adicionales, etiqueta)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(header + '\n' + contenido_procesado + '\n' + footer)
            
        print(f"Procesamiento completado. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    # Configuración
    # archivo_entrada = "salida.html"
    archivo_entrada = "salida_con_titulos.html"
    archivo_salida = "salida_con_titulos.html"
    # palabras_titulo = [ 'TÍTULO', 'TITULO' ]
    # palabras_titulo = [ 'CAPÍTULO', 'CAPITULO' ]
    palabras_titulo = [ 'SECCIÓN', 'SECCION' ]
    lineas_adicionales = 1  
    etiqueta = 'h4'
    
    # Procesar el archivo
    procesar_archivo_html(archivo_entrada, archivo_salida, palabras_titulo, lineas_adicionales, etiqueta) 