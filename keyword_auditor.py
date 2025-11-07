import pandas as pd
import os
import sys
import datetime 
from typing import List, Dict, Any

# --- CONFIGURACIÓN ---
KEYWORD_FILE = 'keywords.xlsx'
REPORT_FOLDER = 'reports'   # Subdirectorio de entrada para los archivos .txt (Reportes resumidos)
INDEX_FOLDER = 'index'      # Subdirectorio de entrada para los archivos .html (Contenido completo)
OUTPUT_FOLDER = 'outputs'   # Subdirectorio de salida para el reporte XLSX
# ---------------------

def get_keywords_from_excel(filepath: str) -> List[str]:
    """
    Lee el archivo XLSX, extrae las palabras clave de la primera columna
    a partir del segundo renglón, las convierte a minúsculas y ELIMINA DUPLICADOS.
    """
    print(f"🔎 Leyendo palabras clave desde: {filepath}")
    try:
        # Lee el archivo completo. header=None, ya que la fila 1 es el encabezado del usuario.
        df = pd.read_excel(filepath, header=None)
        
        # Seleccionar la primera columna (índice 0) y empezar desde la segunda fila (índice 1)
        keywords = df.iloc[1:, 0].dropna().astype(str).str.strip().tolist()
        
        # Convertir todas las palabras clave a minúsculas para una búsqueda sin distinción de mayúsculas
        lower_keywords = [kw.lower() for kw in keywords]
        
        # --- CAMBIO CLAVE: Garantizar que la lista de palabras clave sea ÚNICA ---
        # Convertimos a set para eliminar duplicados, luego a list para mantener la estructura
        unique_keywords = sorted(list(set(lower_keywords)))
        
        if len(lower_keywords) != len(unique_keywords):
            print(f"⚠️ Advertencia: Se eliminaron {len(lower_keywords) - len(unique_keywords)} palabras clave duplicadas.")
        # -------------------------------------------------------------------------
        
        print(f"✅ Palabras clave únicas extraídas con éxito: {len(unique_keywords)} encontradas.")
        return unique_keywords
        
    except FileNotFoundError:
        print(f"❌ ERROR: El archivo de palabras clave '{filepath}' no se encontró.")
        return []
    except Exception as e:
        print(f"❌ ERROR al leer el archivo XLSX: {e}")
        print("Asegúrate de que la columna de palabras clave sea la primera (columna A).")
        return []


def find_report_files(folders: List[str]) -> List[str]:
    """
    Busca archivos con extensiones .txt y .html en la lista de carpetas proporcionadas.
    """
    all_files = []
    # Archivos que sabemos que son de entrada o temporales, no reportes de URL.
    EXCLUDE_FILES = ['urls.txt'] 
    
    print("\n🔍 Buscando archivos de reporte (*.txt y *.html) en los directorios:")
    
    for folder in folders:
        # Comprobar si el subdirectorio existe
        if not os.path.isdir(folder):
            print(f"⚠️ Advertencia: El subdirectorio '{folder}' no fue encontrado. Omitiendo.")
            continue
        
        print(f"  - Inspeccionando: {os.path.abspath(folder)}")
    
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            
            # Solo archivos que terminan en .txt o .html y no están en la lista de exclusión
            if (filename.endswith(".txt") or filename.endswith(".html")) and filename not in EXCLUDE_FILES:
                all_files.append(file_path)
            
    print(f"✅ Total de archivos de reporte/contenido encontrados: {len(all_files)}")
    return all_files


def read_file_content_robustly(file_path: str) -> str:
    """
    Intenta leer el contenido de un archivo usando múltiples codificaciones 
    hasta que una tenga éxito. Esto corrige los errores de 'invalid start byte'.
    """
    encodings = ['utf-8', 'utf-16', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Al tener éxito, devolvemos el contenido en minúsculas
                return f.read().lower()
        except UnicodeDecodeError:
            # Continuamos con la siguiente codificación si falla
            continue
        except Exception as e:
            # Para otros errores (ej. permisos), avisamos y salimos
            print(f"⚠️ Advertencia: Error inesperado al intentar leer '{file_path}' con {encoding}: {e}")
            return ""
            
    # Si llega aquí, falló con todas las codificaciones
    print(f"⚠️ Advertencia CRÍTICA: Falló la lectura de '{os.path.basename(file_path)}' con todas las codificaciones.")
    return ""


def analyze_keywords_in_reports(keywords: List[str], all_files: List[str]) -> List[Dict[str, Any]]:
    """
    Analiza cada palabra clave en todos los archivos de reporte (.txt y .html).
    """
    results: List[Dict[str, Any]] = []
    
    print("\n--- Iniciando Análisis de Coincidencias (Robusto en TXT y HTML) ---")
    
    for keyword in keywords:
        match_count = 0
        found_in_files = []
        
        # Iterar sobre todos los archivos de reporte para una sola palabra clave
        for file_path in all_files:
            # Usamos el nombre del archivo con su extensión y subdirectorio para el reporte final
            # Ejemplo: index/dominio_com.html o reports/dominio_com.txt
            file_name_with_folder = os.path.join(os.path.basename(os.path.dirname(file_path)), os.path.basename(file_path))
            
            # Usamos la nueva función de lectura robusta
            content = read_file_content_robustly(file_path)
            
            if content:
                # Contar las coincidencias
                count = content.count(keyword)
                
                if count > 0:
                    match_count += count
                    found_in_files.append(file_name_with_folder)
                    
        # Almacenar el resultado para esta palabra clave
        # Esta sección garantiza una sola fila por palabra clave ÚNICA
        results.append({
            'keyword': keyword,
            'coincidencias': match_count,
            # La lista se une como cadena para que pandas la guarde fácilmente en una celda
            'archivos_encontrados': ' | '.join(found_in_files) if found_in_files else 'No encontrada'
        })
        
        print(f"Keyword '{keyword}' | Coincidencias: {match_count} | Encontrada en {len(found_in_files)} archivos.")

    print("\n--- Análisis Finalizado ---")
    return results


def save_results_to_xlsx(results: List[Dict[str, Any]], output_file: str, output_folder: str):
    """
    Guarda los resultados del análisis en un archivo XLSX dentro del subdirectorio especificado.
    """
    if not results:
        print("⚠️ No hay resultados para guardar.")
        return

    try:
        # Asegurarse de que la carpeta de salida exista
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"📁 Subdirectorio de salida '{output_folder}' creado.")

        # Construir la ruta completa al archivo de salida
        full_output_path = os.path.join(output_folder, output_file)

        # Convertir la lista de diccionarios a un DataFrame de pandas
        df = pd.DataFrame(results)
        
        # Renombrar columnas para el reporte final
        df.rename(columns={
            'keyword': 'Keyword',
            'coincidencias': 'Número de Coincidencias',
            'archivos_encontrados': 'Archivos Encontrados (TXT/HTML)'
        }, inplace=True)

        # Guardar en archivo XLSX
        df.to_excel(full_output_path, index=False, sheet_name='Reporte Coincidencias')
            
        print(f"\n✅ Reporte XLSX generado con éxito en: {os.path.abspath(full_output_path)}")
        print(f"El reporte se encuentra en la hoja 'Reporte Coincidencias'.")

    except Exception as e:
        print(f"❌ ERROR al guardar el archivo XLSX: {e}")


if __name__ == "__main__":
    
    # 1. Obtener la lista de palabras clave
    # Ahora esta función garantiza que solo se procesen palabras clave únicas
    keywords = get_keywords_from_excel(KEYWORD_FILE)
    
    if not keywords:
        sys.exit("Terminando el script. No se pudieron obtener palabras clave válidas.")
        
    # 2. Encontrar los archivos de reporte de auditoría (TXT y HTML)
    folders_to_inspect = [REPORT_FOLDER, INDEX_FOLDER]
    all_files_to_analyze = find_report_files(folders_to_inspect)
    
    if not all_files_to_analyze:
        sys.exit("Terminando el script. No se encontraron archivos TXT o HTML para analizar en los subdirectorios.")

    # 3. Analizar las palabras clave en los reportes
    analysis_results = analyze_keywords_in_reports(keywords, all_files_to_analyze)
    
    # --- Generar nombre de archivo dinámico: output_YYYYMMDD_HHMMSS.xlsx ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"output_{timestamp}.xlsx"
    # -----------------------------------------------------------------------

    # 4. Guardar los resultados en XLSX, especificando la carpeta de salida
    save_results_to_xlsx(analysis_results, output_filename, OUTPUT_FOLDER)