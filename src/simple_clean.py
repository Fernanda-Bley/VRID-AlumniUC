"""Apply simple cleanup to a configured dataset (SIPA)."""

import csv

from CONFIG import MOJIBAKE_REPLACEMENTS, SOURCE, TITLE_FALLBACK_FIELDS
from clean_duplicates import deduplicate_rows, match_key, standardize_delimited


#cleaning functions
def clean_value(value):
    """Normalize a value: strip whitespace, drop junk, and fix mojibake."""
    value = "" if value is None else str(value).strip()
    return _fix_mojibake(value)


def is_invalid_title(value):
    """Identify spreadsheet error values that are not real titles."""
    if value is None:
        return True
    val = str(value).strip()
    if not val:
        return True
    invalid_set = {
        "#NOMBRE?", "#¿NOMBRE?", "#NAME?",
        "#VALOR!", "#¡VALOR!", "#VALUE!",
        "#N/A", "#REF!", "#DIV/0!", "#NUM!", "#NULL!"
    }
    return val in invalid_set or "NOMBRE?" in val or "VALOR!" in val


def _fix_mojibake(value):
    """Replace broken-encoding sequences with their correct version."""
    for broken, replacement in MOJIBAKE_REPLACEMENTS.items():
        value = value.replace(broken, replacement)
    return value


def deduplicate_delimited(value, delimiter="||"):
    """Remove duplicates within a field of delimiter-separated values."""
    return standardize_delimited(value, delimiter)


def find_author_indexes(header):
    """Return the indexes of all author columns (ES/EN)."""
    return [
        index for index, name in enumerate(header)
        if "author" in name.lower() or "autor" in name.lower()
    ]


def find_title_index(header):
    """Return the index of 'dc.title', or None if it doesn't exist."""
    return header.index("dc.title") if "dc.title" in header else None


def find_title_fallback(header, cleaned_row):
    """Look up, in priority order, a non-empty alternative title."""
    for fallback_name in TITLE_FALLBACK_FIELDS:
        if fallback_name in header:
            fallback_index = header.index(fallback_name)
            if cleaned_row[fallback_index] and not is_invalid_title(
                cleaned_row[fallback_index]
            ):
                return cleaned_row[fallback_index]
    return None


def clean_row(row, header, author_indexes, title_index):
    """Clean a full row: values, duplicate authors, and missing title."""
    cleaned = [clean_value(value) for value in row]

    for index in author_indexes:
        cleaned[index] = deduplicate_delimited(cleaned[index])

    if title_index is not None and is_invalid_title(cleaned[title_index]):
        cleaned[title_index] = ""

    if title_index is not None and not cleaned[title_index]:
        fallback_title = find_title_fallback(header, cleaned)
        if fallback_title:
            cleaned[title_index] = fallback_title

    return cleaned


def has_missing_title(cleaned_row, title_index):
    """Check whether the already-cleaned row still has no title."""
    return title_index is not None and not cleaned_row[title_index].strip()


from author_linkage import (
    build_codpers_map,
    build_codpers_map_from_df,
    process_author_linkage,
    recover_missing_authors_in_df,
)
from normalize_categories import normalize_category_columns, normalize_categories_in_df
from language_normalization import normalize_language_columns, normalize_languages_in_df
from rights_normalization import normalize_rights_columns, normalize_rights_in_df
import pandas as pd


def clean_rows(header, rows):
    """Clean all rows, recover missing authors, normalize categories/Dewey, languages, and rights.

    Returns (cleaned_rows, missing_title_ids).
    """
    author_indexes = find_author_indexes(header)
    title_index = find_title_index(header)

    # 1. Construir catálogo global de personas UC para recuperación de autores Nivel 1
    codpers_map = build_codpers_map(header, rows)

    cleaned_rows = []
    missing_titles = []

    for row in rows:
        # A. Limpieza de valores base y títulos de fallback
        cleaned = clean_row(row, header, author_indexes, title_index)

        # B. Recuperación de autores faltantes (autoruc + codpers_map + autor corporativo)
        cleaned = process_author_linkage(header, cleaned, codpers_map=codpers_map)

        # C. Normalización de categorías, códigos Dewey y ODS
        cleaned = normalize_category_columns(header, cleaned)

        # D. Normalización de códigos de idioma ISO (639-1)
        cleaned = normalize_language_columns(header, cleaned)

        # E. Normalización de derechos de acceso y permisos
        cleaned = normalize_rights_columns(header, cleaned)

        if has_missing_title(cleaned, title_index):
            missing_titles.append(row[0])
        cleaned_rows.append(cleaned)

    return cleaned_rows, missing_titles


def clean_df(df: pd.DataFrame, codpers_map: dict = None) -> tuple:
    """
    Limpia y normaliza un DataFrame de Pandas integrando todos los módulos:
    - Limpieza de Mojibake y espacios en blanco en campos de texto relevante
    - Deduplicación de campos de autor
    - Recuperación de títulos mediante fallback
    - Recuperación de autores ausentes con codpers_map
    - Normalización de categorías, Dewey, ODS, idiomas ISO y derechos de acceso.

    Retorna (df_limpio, lista_id_sin_titulo).
    """
    df = df.copy()

    # 1. Limpieza base de Mojibake enfocada solo en columnas de texto metadata propensas a corrupción
    text_mojibake_cols = [
        c for c in df.columns 
        if c in ("dc.title", "dc.description.abstract", "dc.subject", "dc.publisher", "dc.information.autoruc")
        or "title" in c.lower() or "abstract" in c.lower()
    ]
    
    for col in text_mojibake_cols:
        col_s = df[col].fillna("").astype(str)
        if col_s.str.contains(r"[ÃÂâ√]", regex=True, na=False).any():
            for broken, replacement in MOJIBAKE_REPLACEMENTS.items():
                col_s = col_s.str.replace(broken, replacement, regex=False)
            df[col] = col_s.str.strip()

    # 2. Deduplicar campos multivalor de autores únicamente si contienen el delimitador ||
    author_cols = [c for c in df.columns if "author" in c.lower() or "autor" in c.lower()]
    for col in author_cols:
        col_s = df[col].fillna("").astype(str)
        if col_s.str.contains(r"\|\|", regex=True, na=False).any():
            df[col] = col_s.apply(deduplicate_delimited)

    # 3. Limpieza y Fallback de Títulos
    missing_titles = []
    if "dc.title" in df.columns:
        df["dc.title"] = df["dc.title"].apply(lambda t: "" if is_invalid_title(t) else t)

        for fallback_col in TITLE_FALLBACK_FIELDS:
            if fallback_col in df.columns:
                mask_missing = (df["dc.title"] == "") & (df[fallback_col] != "") & (~df[fallback_col].apply(is_invalid_title))
                df.loc[mask_missing, "dc.title"] = df.loc[mask_missing, fallback_col]

        id_col = df.columns[0]
        missing_titles = df.loc[df["dc.title"] == "", id_col].tolist()

    # 4. Construcción de catálogo y recuperación de autores
    if codpers_map is None:
        codpers_map = build_codpers_map_from_df(df)

    df = recover_missing_authors_in_df(df, codpers_map=codpers_map)

    # 5. Normalizaciones de módulos especializados
    df = normalize_categories_in_df(df)
    df = normalize_languages_in_df(df)
    df = normalize_rights_in_df(df)

    return df, missing_titles



def drop_empty_columns_df(df: pd.DataFrame) -> tuple:
    """Elimina columnas completamente vacías en un DataFrame de Pandas."""
    empty_cols = [col for col in df.columns if (df[col].fillna("").astype(str).str.strip() == "").all()]
    df_filtered = df.drop(columns=empty_cols)
    return df_filtered, empty_cols


def drop_empty_columns(header, rows, null_threshold=0.99):
    """Remove columns whose empty-value ratio meets ``null_threshold``.

    Returns (filtered_header, filtered_rows, removed_columns).
    """
    if not 0 <= null_threshold <= 1:
        raise ValueError("null_threshold must be between 0 and 1")

    row_count = len(rows)
    kept_indexes = [
        index for index, name in enumerate(header)
        if row_count == 0
        or sum(not row[index].strip() for row in rows) / row_count < null_threshold
    ]
    removed_columns = [
        name for index, name in enumerate(header) if index not in kept_indexes
    ]

    filtered_header = [header[index] for index in kept_indexes]
    filtered_rows = [[row[index] for index in kept_indexes] for row in rows]

    return filtered_header, filtered_rows, removed_columns


def delete_empty_rows(rows):
    """Remove rows where every column is empty."""
    return [row for row in rows if any(value.strip() for value in row)]

# Writing results
def write_csv(path, header, rows):
    """Write the cleaned CSV to disk, creating the directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(header)
        writer.writerows(rows)


def write_log(path, title, items):
    """Write a generic log: source, title, count, and item details."""
    with path.open("w", encoding="utf-8") as log:
        log.write(f"Source: {SOURCE}\n{title}: {len(items)}\n")
        log.writelines(f"{item!r}\n" for item in items)


