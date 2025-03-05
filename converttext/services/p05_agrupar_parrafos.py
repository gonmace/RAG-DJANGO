import re

def agrupar_parrafos(texto):
    """
    Agrupa párrafos contiguos en un solo párrafo, eliminando saltos de línea innecesarios.
    
    Args:
        texto (str): Texto HTML a procesar
        
    Returns:
        str: Texto con los párrafos agrupados
    """
    # Dividir el texto en líneas y limpiar espacios
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
    resultado = []
    parrafo_actual = []
    
    for linea in lineas:
        # Verificar si la línea es un párrafo
        if linea.startswith('<p>') and linea.endswith('</p>'):
            # Extraer el contenido del párrafo
            contenido = re.sub(r'<p>(.*?)</p>', r'\1', linea)
            parrafo_actual.append(contenido)
        else:
            # Si hay párrafos acumulados, unirlos
            if parrafo_actual:
                resultado.append(f"<p>{' '.join(parrafo_actual)}</p>")
                parrafo_actual = []
            resultado.append(linea)
    
    # Procesar cualquier párrafo pendiente al final
    if parrafo_actual:
        resultado.append(f"<p>{' '.join(parrafo_actual)}</p>")
    
    return '\n'.join(resultado)

def procesar_archivo_html(archivo_entrada, archivo_salida):
    """
    Procesa un archivo HTML para agrupar párrafos contiguos.
    
    Args:
        archivo_entrada (str): Ruta del archivo HTML de entrada
        archivo_salida (str): Ruta del archivo HTML de salida
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
        contenido_procesado = agrupar_parrafos(body)
        
        # Guardar el resultado
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(header + '\n' + contenido_procesado + '\n' + footer)
            
        print(f"Procesamiento completado. Archivo guardado como: {archivo_salida}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    # Configuración
    archivo_entrada = "salida_con_saltos_linea.html"
    archivo_salida = "salida_con_parrafos_agrupados.html"
    
    # Procesar el archivo
    procesar_archivo_html(archivo_entrada, archivo_salida) 