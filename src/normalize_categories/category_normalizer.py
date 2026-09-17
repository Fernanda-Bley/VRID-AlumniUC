"""
Módulo principal de normalización de categorías repetidas y códigos Dewey inconsistentes.
Ubicación: src/normalize_categories/category_normalizer.py
"""

from .dewey_mapping import (
    CATEGORY_MOJIBAKE,
    DEWEY_CODE_TO_SPANISH,
    ODS_ENGLISH_TO_SPANISH,
    ODS_SPANISH_TO_ENGLISH,
)



def clean_mojibake_text(text: str) -> str:
    """Corrige caracteres corruptos por doble decodificación UTF-8 / Latin-1."""
    if not text:
        return ""
    
    # Reemplazo de mapa estático
    for broken, fixed in CATEGORY_MOJIBAKE.items():
        if broken in text:
            text = text.replace(broken, fixed)
            
    # Casos comunes de 'Religin' -> 'Religión'
    text = text.replace("Religin", "Religión")
    text = text.replace("Ingeniera", "Ingeniería")
    text = text.replace("Astronoma", "Astronomía")
    text = text.replace("Educacin", "Educación")
    text = text.replace("Biologa", "Biología")
    text = text.replace("Economa", "Economía")
    text = text.replace("fsica", "física")
    text = text.replace("qumica", "química")
    text = text.replace("Matemticas", "Matemáticas")
    text = text.replace("Filosofa", "Filosofía")
    text = text.replace("Psicologa", "Psicología")
    text = text.replace("tica", "Ética")
    text = text.replace("innovacin", "innovación")
    text = text.replace("Energa", "Energía")
    text = text.replace("Accin", "Acción")
    text = text.replace("Produccin", "Producción")

    return text.strip()


import re


def normalize_dewey_pair(ddc_code: str, dewey_text: str):
    """
    Recibe el código numérico Dewey (dc.subject.ddc) y su descripción (dc.subject.dewey[es_ES]).
    Normaliza formatos mixtos: comas decimales, ceros a la izquierda y casillas contaminadas.
    Devuelve la tupla normalizada (código_numérico, descripción_español).
    """
    ddc_code = clean_mojibake_text(str(ddc_code or "").strip())
    dewey_text = clean_mojibake_text(str(dewey_text or "").strip())
    if dewey_text.endswith("."):
        dewey_text = dewey_text[:-1].rstrip()

    # 1. Estandarizar separador decimal de coma a punto (ej. '512,942' -> '512.942')
    ddc_code = ddc_code.replace(",", ".")

    # 2. Extraer código numérico si la casilla viene contaminada con texto (ej. '610||Medicina y salud')
    if not ddc_code.isdigit() and not re.match(r"^\d+\.\d+$", ddc_code):
        num_match = re.search(r"\b(\d{1,3}(?:\.\d+)?)\b", ddc_code)
        if num_match:
            ddc_code = num_match.group(1)
        else:
            # Si no hay número válido, limpiar si era un URL o texto basura
            if ddc_code.startswith("http") or len(ddc_code) > 20:
                ddc_code = ""

    # 3. Rellenar ceros a la izquierda si el código tiene 1 o 2 dígitos (ej. '70' -> '070', '0' -> '000')
    if ddc_code.isdigit() and len(ddc_code) < 3:
        ddc_code = ddc_code.zfill(3)

    # Extraer código de 3 dígitos base (ej. '616.0475' -> '610', '338.1' -> '330')
    clean_code = ddc_code.split(".")[0] if "." in ddc_code else ddc_code

    # Si la descripción de texto es numérico (ej. '610'), limpiarla para buscar el nombre real
    if dewey_text.isdigit():
        clean_code = clean_code or dewey_text.zfill(3)
        dewey_text = ""

    # Buscar descripción estándar si no existe o si se identificó un código numérico conocido
    if clean_code in DEWEY_CODE_TO_SPANISH:
        expected_text = DEWEY_CODE_TO_SPANISH[clean_code]
        if not dewey_text or dewey_text == clean_code:
            dewey_text = expected_text
    elif clean_code and clean_code.isdigit() and len(clean_code) >= 2:
        # Aproximar a la centena base de 3 dígitos (ej. 340 -> 300) si no está en la tabla exacta
        base_hundred = clean_code[0] + "00"
        if base_hundred in DEWEY_CODE_TO_SPANISH and not dewey_text:
            dewey_text = DEWEY_CODE_TO_SPANISH[base_hundred]

    return clean_code, dewey_text



def normalize_ods_tag(ods_val: str, target_lang: str = "es") -> str:
    """Normaliza y mantiene la marca ODS en el idioma objetivo ('es' para español, 'en' para inglés)."""
    if not ods_val:
        return ""
    
    ods_val = clean_mojibake_text(ods_val)
    
    if target_lang == "es":
        # Convertir a español si viene en inglés
        if ods_val in ODS_ENGLISH_TO_SPANISH:
            return ODS_ENGLISH_TO_SPANISH[ods_val]
    elif target_lang == "en":
        # Convertir a inglés si viene en español
        if ods_val in ODS_SPANISH_TO_ENGLISH:
            return ODS_SPANISH_TO_ENGLISH[ods_val]
        
    return ods_val


def normalize_subject_cell(cell_val: str, delimiter="||") -> str:
    """
    Normaliza una celda de categorías/materias:
    - Separa valores por el delimitador (ej. '||')
    - Limpia Mojibake y elimina puntos finales sobrantes
    - Deduplica manteniendo el orden original
    """
    if not cell_val:
        return ""
    
    items = cell_val.split(delimiter)
    seen = set()
    cleaned_items = []
    
    for item in items:
        cleaned = clean_mojibake_text(item)
        
        # Eliminar punto final si existe (ej. 'Derecho Constitucional.' -> 'Derecho Constitucional')
        if cleaned.endswith("."):
            cleaned = cleaned[:-1].rstrip()
            
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            cleaned_items.append(cleaned)
            
    return delimiter.join(cleaned_items)


def normalize_category_columns(header: list, row: list) -> list:
    """
    Aplica la normalización de categorías y códigos Dewey a una fila completa.
    """
    row_copy = list(row)
    
    # Indexar columnas relevantes
    ddc_idx = header.index("dc.subject.ddc") if "dc.subject.ddc" in header else None
    dewey_es_idx = header.index("dc.subject.dewey[es_ES]") if "dc.subject.dewey[es_ES]" in header else None
    ods_idx = header.index("dc.subject.ods") if "dc.subject.ods" in header else None
    odspa_idx = header.index("dc.subject.odspa") if "dc.subject.odspa" in header else None
    
    # 1. Normalizar par Dewey (Código y Texto)
    if ddc_idx is not None or dewey_es_idx is not None:
        raw_code = row_copy[ddc_idx] if ddc_idx is not None else ""
        raw_text = row_copy[dewey_es_idx] if dewey_es_idx is not None else ""
        
        norm_code, norm_text = normalize_dewey_pair(raw_code, raw_text)
        
        if ddc_idx is not None:
            row_copy[ddc_idx] = norm_code
        if dewey_es_idx is not None:
            row_copy[dewey_es_idx] = norm_text

    # 2. Normalizar ODS respetando el idioma oficial de cada columna (Inglés en dc.subject.ods, Español en dc.subject.odspa)
    if ods_idx is not None and row_copy[ods_idx]:
        row_copy[ods_idx] = normalize_ods_tag(row_copy[ods_idx], target_lang="en")
    if odspa_idx is not None and row_copy[odspa_idx]:
        row_copy[odspa_idx] = normalize_ods_tag(row_copy[odspa_idx], target_lang="es")


    # 3. Normalizar celdas de materias generales
    for idx, name in enumerate(header):
        if "subject" in name.lower() and idx not in (ddc_idx, dewey_es_idx, ods_idx, odspa_idx):
            if row_copy[idx]:
                row_copy[idx] = normalize_subject_cell(row_copy[idx])
                
    return row_copy
