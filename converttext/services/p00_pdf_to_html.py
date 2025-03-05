import pdfplumber
import sys

def pdf_a_html(archivo_pdf, archivo_salida, eliminar_tablas=True):
    """
    Convierte un archivo PDF a formato HTML usando pdfplumber.
    
    Args:
        archivo_pdf (str): Ruta del archivo PDF de entrada
        archivo_salida (str): Ruta del archivo HTML de salida
        eliminar_tablas (bool): Si es True, convierte las tablas en párrafos. Por defecto es True.
    """
    try:
        print(f"Convirtiendo {archivo_pdf} a HTML...")

        # Cabecera del HTML
        html_header = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Convertido</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        p {
            margin-bottom: 0.5em;
        }
        h2 {
            font-size: 1.5em;
            font-weight: bold;
            margin: 1em 0 0.5em 0;
            color: red;
        }
        h3 {
            font-size: 1.2em;
            font-weight: bold;
            margin: 0.8em 0 0.4em 0;
            color: green;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        td, th {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f5f5f5;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 10px 0;
        }
    </style>
</head>
<body>
"""

        # Procesar el PDF
        html_content = []
        with pdfplumber.open(archivo_pdf) as pdf:
            for page in pdf.pages:
                # Extraer texto con formato
                text = page.extract_text()
                
                # Procesar tablas si existen
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if eliminar_tablas:
                            # Convertir cada celda en un párrafo
                            for row in table:
                                for cell in row:
                                    if cell and cell.strip():
                                        # Procesar cada línea de la celda como un párrafo separado
                                        for line in cell.strip().split('\n'):
                                            if line.strip():
                                                html_content.append(f"<p>{line.strip()}</p>")
                        else:
                            # Mantener el formato de tabla original
                            table_html = ["<table>"]
                            for row in table:
                                table_html.append("<tr>")
                                for cell in row:
                                    table_html.append(f"<td>{cell if cell else ''}</td>")
                                table_html.append("</tr>")
                            table_html.append("</table>")
                            html_content.append("\n".join(table_html))
                
                # Procesar el texto línea por línea
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            # Detectar si es un título basado en palabras clave y formato
                            if line.upper().startswith(('TÍTULO', 'TITULO', 'CAPÍTULO', 'CAPITULO')):
                                html_content.append(f"<h2>{line}</h2>")
                            elif line.upper().startswith(('SECCIÓN', 'SECCION', 'ARTÍCULO', 'ARTICULO')):
                                html_content.append(f"<h3>{line}</h3>")
                            else:
                                # Procesar cada línea como un párrafo separado
                                for subline in line.split('\n'):
                                    if subline.strip():
                                        html_content.append(f"<p>{subline.strip()}</p>")

        # Concatenar todo el HTML
        final_html = html_header + "\n".join(html_content) + "</body>\n</html>"
        
        # Guardar el HTML
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(final_html)

        print(f"Conversión completada. Archivo guardado como: {archivo_salida}")

    except Exception as e:
        print(f"Error durante la conversión: {str(e)}")

if __name__ == "__main__":
    archivo_pdf = "COD.pdf"
    archivo_salida = "salida.html"
    pdf_a_html(archivo_pdf, archivo_salida, eliminar_tablas=True)
