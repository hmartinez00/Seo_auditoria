# 🔍 Herramienta de Auditoría SEO y Análisis de Palabras Clave (Python)

Este proyecto consiste en un conjunto de scripts en Python diseñados para automatizar tareas clave de análisis SEO:
1.  **Auditoría Técnica On-Page:** Extracción de metadatos, encabezados, y contenido HTML de listas de URLs.
2.  **Análisis de Coincidencias de Palabras Clave:** Conteo de ocurrencias de palabras clave específicas dentro del contenido extraído, generando un informe consolidado.

## 📦 Estructura del Proyecto

```

.
├── seo\_auditor.py        \# Script principal de auditoría On-Page (Descarga y Parseo)
├── keyword\_auditor.py    \# Script de análisis de palabras clave (Genera reporte XLSX)
├── urls.txt              \# ENTRADA: Lista de URLs a auditar (Una por línea)
├── keywords.xlsx         \# ENTRADA: Lista de palabras clave a buscar (Columna A)
├── reports/              \# SALIDA: Informes TXT de la auditoría On-Page
├── index/                \# SALIDA: Archivos HTML completos descargados
└── outputs/              \# SALIDA: Reporte final XLSX de coincidencias de keywords

```

## ⚙️ Requisitos e Instalación

Este proyecto requiere Python 3.x y las siguientes librerías:

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

## 🚀 1. Script de Auditoría On-Page (`seo_auditor.py`)

Este script se encarga de descargar las páginas web y extraer los elementos clave de SEO (título, meta descripción, encabezados, texto en etiquetas `<span>`, etc.), guardando los resultados para el posterior análisis de palabras clave.

### Archivos de Entrada:

| Archivo | Propósito | Formato |
| :--- | :--- | :--- |
| `urls.txt` | Lista de URLs a procesar. Una URL por línea. | Texto plano (.txt) |

### Archivos de Salida:

| Directorio | Contenido |
| :--- | :--- |
| `reports/` | Archivos `.txt` con el resumen de la auditoría SEO por URL. |
| `index/` | Archivos `.html` con el código fuente completo de cada URL. |

### Ejecución:

1.  Asegúrate de que el archivo `urls.txt` contenga las URLs que deseas auditar.
2.  Ejecuta el script:

<!-- end list -->

```bash
python seo_auditor.py
```

## 📊 2. Script de Análisis de Palabras Clave (`keyword_auditor.py`)

Este script utiliza el contenido descargado por `seo_auditor.py` (archivos en `reports/` e `index/`) y lo compara con tu lista de palabras clave para generar un reporte consolidado en XLSX.

### Archivos de Entrada:

| Archivo | Propósito | Requisito Clave |
| :--- | :--- | :--- |
| `keywords.xlsx` | Lista de palabras clave para auditar. | Las palabras clave deben estar en la **Columna A**, a partir de la fila 2. El script elimina automáticamente los duplicados. |
| `reports/` y `index/` | Contenido generado por `seo_auditor.py`. | Los archivos deben existir para que la auditoría funcione. |

### Archivos de Salida:

| Directorio | Contenido |
| :--- | :--- |
| `outputs/` | Archivo `.xlsx` con la estructura: `[Keyword]`, `[Número de Coincidencias]`, `[Archivos Encontrados]`. |

### Ejecución:

1.  Asegúrate de haber ejecutado previamente `seo_auditor.py` para tener contenido en `reports/` e `index/`.
2.  Asegúrate de que el archivo `keywords.xlsx` contenga tu lista de términos.
3.  Ejecuta el script:

<!-- end list -->

```bash
python keyword_auditor.py
```

-----

## 🔧 Notas de Desarrollo y Mantenimiento

  * **Codificación Robusta:** Ambos scripts incluyen lógica para manejar diferentes codificaciones (`utf-8`, `latin-1`, etc.) al leer archivos de entrada, minimizando errores de acentos o caracteres especiales.
  * **Extracción Detallada:** `seo_auditor.py` extrae metadatos clave, encabezados (`h1`, `h2`, `h3`) y el texto contenido en las etiquetas semánticamente importantes `<span />`.
  * **Manejo de Duplicados:** El script `keyword_auditor.py` elimina duplicados de la lista de palabras clave para un análisis más limpio.

<!-- end list -->

## 💡 Valoración de negocios según Google My Business

El indicador más común y aceptado que combina la **calificación de estrellas** y el **número de reseñas (reviews)** para medir la calidad y la credibilidad es el concepto de **Valoración Ponderada** o **Credibilidad de la Calificación**.

Aunque no existe una única "fórmula oficial" estandarizada por Google que se haga pública para este fin, la forma más lógica y utilizada para crear un indicador propio para tu lista es aplicando una **ponderación** a la calificación de estrellas basada en el volumen de reseñas.

### 📝 Propuesta de Indicador (Fórmula Sugerida)

Una forma efectiva de combinar ambos parámetros es utilizando una fórmula que favorezca las calificaciones altas *respaldadas por un gran número de reseñas*.

Un indicador muy simple y funcional que puedes calcular para cada negocio es el **Puntaje de Confianza de la Reseña (PCR)**.

$$
\text{PCR} = \text{Calificación de Estrellas} \times \left(1 - \frac{1}{\text{Número Total de Reseñas} + K}\right)
$$

Donde:

* **Calificación de Estrellas:** El promedio de estrellas del negocio (ej. 4.5).
* **Número Total de Reseñas:** El conteo de reseñas.
* **$K$ (Constante de Amortiguación):** Es un número que decides para darle un "impulso" inicial a los negocios, o para establecer un umbral de confianza mínimo. Un valor común podría ser **$K=5$** o **$K=10$**.