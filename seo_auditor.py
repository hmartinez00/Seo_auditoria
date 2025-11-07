import requests
from bs4 import BeautifulSoup
import sys
import urllib3
import os
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse 

# Deshabilita la advertencia de petición insegura
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN DE ARCHIVOS Y CARPETAS ---
URL_LIST_FILE = 'urls.txt'
REPORT_FOLDER = 'reports'  # Directorio para los informes de auditoría TXT
INDEX_FOLDER = 'index'    # Nuevo directorio para guardar el HTML completo
# ---------------------------------------------

def get_filename_base(url: str) -> str:
    """
    Genera un nombre de archivo seguro basado en el dominio de la URL.
    """
    safe_url = url.replace('\x00', '')
    parsed_url = urlparse(safe_url)
    
    # Usamos el netloc (hostname)
    filename_base = parsed_url.netloc.split(':')[0] 
    
    if not filename_base:
        # Si no hay host (ej: solo ruta), usamos una versión limpia de la ruta.
        path_part = parsed_url.path.strip('/').replace('/', '_')
        filename_base = path_part if path_part else "analisis_web"
        
    # Saneamiento final
    return filename_base.replace('.', '_').replace('-', '_')


def extract_seo_data(url: str) -> Tuple[Dict[str, Any], str]:
    """
    Descarga el contenido de la URL y extrae los datos clave de SEO on-page.
    
    Args:
        url: La URL de la página a analizar.
        
    Returns:
        Una tupla: (diccionario de resultados SEO, contenido HTML completo).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    results: Dict[str, Any] = {
        'url_analizada': url,
        'title': 'No encontrado',
        'meta_description': 'No encontrado',
        'meta_keywords': 'No encontrado',
        'canonical': 'No encontrado',
        'h1': [],
        'h2': [],
        'h3': [],
        'otras_meta': {},
        'error': None
    }
    html_content = "" # Inicializar el contenido HTML

    try:
        # 1. Realizar la petición HTTP
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status() 

        # --- AJUSTE CLAVE PARA LA CODIFICACIÓN (Solución de Acentos/Ñ) ---
        response.encoding = 'utf-8'
        html_content = response.text # Guardamos el HTML completo
        
        soup = BeautifulSoup(html_content, 'html.parser')
        # ------------------------------------------------------------------

        # 2. Extracción de <title>
        title_tag = soup.find('title')
        if title_tag:
            results['title'] = title_tag.get_text(strip=True)

        # 3. Extracción de Meta Tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '').strip()

            if name == 'description':
                results['meta_description'] = content
            elif name == 'keywords':
                results['meta_keywords'] = content
            elif name:
                results['otras_meta'][name] = content
            elif property_attr:
                results['otras_meta'][property_attr] = content

        # 4. Extracción de Canonical Link
        canonical_tag = soup.find('link', rel='canonical')
        if canonical_tag:
            results['canonical'] = canonical_tag.get('href')

        # 5. Extracción de Encabezados (H1, H2, H3)
        def extract_headers(tag_name: str) -> List[str]:
            """Función auxiliar para extraer el texto de los encabezados."""
            return [tag.get_text(strip=True) for tag in soup.find_all(tag_name)]

        results['h1'] = extract_headers('h1')
        results['h2'] = extract_headers('h2')
        results['h3'] = extract_headers('h3')

    except requests.exceptions.RequestException as e:
        results['error'] = f"Error al descargar la página o tiempo de espera agotado: {e}"
    except Exception as e:
        if "Failed to parse" in str(e):
             results['error'] = f"Error de formato de URL (posiblemente por codificación incorrecta del archivo urls.txt): {e}"
        else:
             results['error'] = f"Ocurrió un error general durante el parseo: {e}"

    return results, html_content # Retorna resultados y el HTML

def format_seo_report(results: Dict[str, Any]) -> str:
    """
    Formatea los resultados de la auditoría SEO en una cadena de texto para consola y archivo.
    """
    report_lines = []
    
    # Encabezado
    separator = "=" * 60
    report_lines.append(separator)
    report_lines.append(f"       ✅ Auditoría SEO On-Page: {results['url_analizada']}")
    report_lines.append(separator)

    # Errores
    if results.get('error'):
        report_lines.append(f"❌ ERROR: {results['error']}")
        report_lines.append(separator)
        return "\n".join(report_lines)

    # MÉTADATOS PRINCIPALES
    report_lines.append("\n--- MÉTADATOS PRINCIPALES (HEAD) ---")
    report_lines.append(f"TITLE:           {results['title']}")
    report_lines.append(f"Descripción Meta:  {results['meta_description']}")
    report_lines.append(f"Keywords Meta:   {results['meta_keywords']}")
    report_lines.append(f"Canonical URL:   {results['canonical']}")

    # ENCABEZADOS DE CONTENIDO
    report_lines.append("\n--- ESTRUCTURA DE ENCABEZADOS ---")
    
    def append_headers(tag_name, headers):
        report_lines.append(f"{tag_name.upper()} ({len(headers)}):")
        if headers:
            for i, h in enumerate(headers, 1):
                report_lines.append(f"  {i}. {h[:80]}{'...' if len(h) > 80 else ''}")
        else:
            report_lines.append(f"  No se encontraron etiquetas <{tag_name}>.")

    append_headers('h1', results['h1'])
    append_headers('h2', results['h2'])
    append_headers('h3', results['h3'])
        
    # OTRAS METATAGS
    report_lines.append("\n--- OTRAS METATAGS (Robots, OG, etc.) ---")
    if results['otras_meta']:
        for key, value in results['otras_meta'].items():
            report_lines.append(f"  {key}: {value[:100]}{'...' if len(value) > 100 else ''}")
    else:
        report_lines.append("  No se encontraron meta tags adicionales (robots, Open Graph, etc.).")
    
    return "\n".join(report_lines)

def save_full_html(url: str, html_content: str):
    """
    Guarda el contenido HTML completo en un archivo dentro del directorio 'index'.
    """
    if not html_content:
        # No guardamos si el contenido está vacío (generalmente por un error de conexión)
        return 

    try:
        filename_base = get_filename_base(url)
        filename = f"{filename_base}.html" 
        
        # 1. Asegurarse de que el directorio 'index' exista
        if not os.path.exists(INDEX_FOLDER):
            os.makedirs(INDEX_FOLDER)
            print(f"📁 Subdirectorio '{INDEX_FOLDER}' creado.")

        # 2. Construir la ruta completa al archivo de salida
        full_output_path = os.path.join(INDEX_FOLDER, filename)


        # Guardar el HTML
        with open(full_output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ HTML completo guardado en: {os.path.abspath(full_output_path)}")
        
    except Exception as e:
        print(f"\n❌ Error al guardar el archivo HTML: {e}", file=sys.stderr)


def print_and_save_seo_report(results: Dict[str, Any], html_content: str):
    """
    Imprime los resultados de la auditoría SEO en la consola, guarda el informe TXT 
    y luego llama a la función para guardar el HTML.
    """
    report = format_seo_report(results)
    print(report)
    
    # Lógica de guardado del informe TXT
    if not results.get('error'): # Solo guardar TXT si no hubo error de conexión
        try:
            filename_base = get_filename_base(results['url_analizada'])
            filename = f"{filename_base}.txt" 
            
            # 1. Asegurarse de que el directorio 'reports' exista
            if not os.path.exists(REPORT_FOLDER):
                os.makedirs(REPORT_FOLDER)
                print(f"📁 Subdirectorio '{REPORT_FOLDER}' creado.")

            # 2. Construir la ruta completa al archivo de salida
            full_output_path = os.path.join(REPORT_FOLDER, filename)


            # Guardar el informe TXT
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(report)
                
            print(f"\n✅ Informe TXT guardado con éxito en: {os.path.abspath(full_output_path)}")
            
        except Exception as e:
            print(f"\n❌ Error al guardar el archivo de informe TXT: {e}", file=sys.stderr)

    # Lógica de guardado del HTML completo
    save_full_html(results['url_analizada'], html_content)


def get_urls_to_analyze(default_url: str) -> List[str]:
    """
    Determina la lista de URLs a analizar, priorizando argumentos de línea de comandos,
    luego el archivo de lista, y finalmente la URL por defecto.
    """
    urls_list = []
    
    # 1. Chequea si hay un argumento en línea de comandos (una sola URL)
    if len(sys.argv) > 1:
        url_argument = sys.argv[1].replace('\x00', '')
        urls_list.append(url_argument)
        return urls_list

    # 2. Chequea si existe el archivo de lista de URLs
    if os.path.exists(URL_LIST_FILE):
        print(f"🔎 Analizando URLs desde el archivo: {URL_LIST_FILE}")
        
        encodings = ['utf-8', 'utf-16', 'latin-1']
        found_urls = False
        
        for encoding in encodings:
            try:
                with open(URL_LIST_FILE, 'r', encoding=encoding) as f:
                    for line in f:
                        url = line.strip().replace('\x00', '')
                        
                        if url and not url.startswith('#'): 
                            urls_list.append(url)
                    found_urls = True
                    break 
            except UnicodeDecodeError:
                print(f"Intentando con codificación {encoding} fallida. Probando siguiente...")
                urls_list = []
            except Exception as e:
                print(f"Error inesperado al leer el archivo con {encoding}: {e}", file=sys.stderr)
                urls_list = []
                break

        if found_urls and urls_list:
            return urls_list
        print(f"❌ ERROR: Falló la lectura del archivo {URL_LIST_FILE} con todas las codificaciones probadas. Asegúrate de que está guardado como texto simple.")


    # 3. Si no hay argumentos ni archivo de lista, usa la URL por defecto
    print(f"⚠️ No se encontró {URL_LIST_FILE} o el archivo estaba vacío/corrupto. Analizando URL por defecto.")
    return [default_url]


if __name__ == "__main__":
    # URL de fallback/ejemplo si no se usa lista ni argumento
    default_url_example = 'https://www.google.com/' 
    
    # Obtener la lista de URLs a procesar
    urls_to_process = get_urls_to_analyze(default_url_example)

    # Iterar sobre cada URL en la lista
    for url_to_analyze in urls_to_process:
        # Aseguramos que la URL comience con http:// o https:// para peticiones válidas
        if not url_to_analyze.startswith(('http://', 'https://')):
            url_to_analyze = 'https://' + url_to_analyze

        # Ejecutar la extracción (ahora devuelve datos SEO Y HTML)
        seo_data, full_html = extract_seo_data(url_to_analyze)
        
        # Imprimir y guardar los resultados (TXT y HTML)
        print_and_save_seo_report(seo_data, full_html)
        
        # Separador para la consola si hay múltiples URLs
        if len(urls_to_process) > 1:
            print("\n" + "~" * 60 + "\n")