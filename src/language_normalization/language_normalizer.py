"""
Módulo de Estandarización de Códigos de Idioma ISO.
Ubicación: src/language_normalization/language_normalizer.py
"""

# Mapeo ISO 639-2 (3 letras) y nombres completos -> ISO 639-1 (2 letras estándar DSpace)
LANGUAGE_MAP = {
    "eng": "en",
    "english": "en",
    "en_us": "en",
    "en_gb": "en",
    "spa": "es",
    "spanish": "es",
    "español": "es",
    "es_es": "es",
    "es_cl": "es",
    "por": "pt",
    "portuguese": "pt",
    "portugués": "pt",
    "fra": "fr",
    "french": "fr",
    "francés": "fr",
    "deu": "de",
    "german": "de",
    "alemán": "de",
    "ita": "it",
    "italian": "it",
    "italiano": "it",
    "und": "und",  # Indeterminado / Undetermined
}


def normalize_language_code(lang_str: str, delimiter: str = "||") -> str:
    """
    Normaliza los códigos de idioma a ISO 639-1 (2 letras):
    - Convierte 'eng' -> 'en', 'spa' -> 'es'
    - Deduplica celdas multivalor 'es||es' -> 'es'
    """
    if not lang_str or not str(lang_str).strip():
        return ""

    tokens = str(lang_str).split(delimiter)
    seen = set()
    cleaned_langs = []

    for token in tokens:
        clean = token.strip().lower()
        # Mapear al código estándar de 2 letras si existe en el diccionario
        std_lang = LANGUAGE_MAP.get(clean, clean)
        
        if std_lang and std_lang not in seen:
            seen.add(std_lang)
            cleaned_langs.append(std_lang)

    return delimiter.join(cleaned_langs)


def normalize_language_columns(header: list, row: list) -> list:
    """
    Normaliza todas las columnas de idioma en la fila (ej. dc.language.iso).
    """
    row_copy = list(row)
    for idx, name in enumerate(header):
        if "language" in name.lower():
            if row_copy[idx]:
                row_copy[idx] = normalize_language_code(row_copy[idx])
    return row_copy
