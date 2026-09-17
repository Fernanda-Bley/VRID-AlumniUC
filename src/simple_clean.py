"""Apply simple cleanup to a configured dataset (SIPA)."""

import csv

from CONFIG import FIELD_SIZE_LIMIT, MOJIBAKE_REPLACEMENTS, SOURCE, TITLE_FALLBACK_FIELDS


#cleaning functions
def clean_value(value):
    """Normalize a value: strip whitespace, drop junk, and fix mojibake."""
    value = "" if value is None else str(value).strip()
    return _fix_mojibake(value)


def is_invalid_title(value):
    """Identify spreadsheet error values that are not real titles."""
    return value in {"#�NOMBRE?", "#NOMBRE?", "#�VALOR!", "#VALOR!"}


def _fix_mojibake(value):
    """Replace broken-encoding sequences with their correct version."""
    for broken, replacement in MOJIBAKE_REPLACEMENTS.items():
        value = value.replace(broken, replacement)
    return value


def deduplicate_delimited(value, delimiter="||"):
    """Remove duplicates within a field of delimiter-separated values."""
    seen = set()
    result = []
    for item in value.split(delimiter):
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return delimiter.join(result)


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


from author_linkage import build_codpers_map, process_author_linkage
from normalize_categories import normalize_category_columns
from language_normalization import normalize_language_columns
from rights_normalization import normalize_rights_columns


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



def drop_empty_columns(header, rows):
    """Remove columns where every row ended up empty.

    Returns (filtered_header, filtered_rows, removed_columns).
    """
    kept_indexes = [
        index for index, name in enumerate(header)
        if any(row[index].strip() for row in rows)
    ]
    removed_columns = [
        name for index, name in enumerate(header) if index not in kept_indexes
    ]

    filtered_header = [header[index] for index in kept_indexes]
    filtered_rows = [[row[index] for index in kept_indexes] for row in rows]

    return filtered_header, filtered_rows, removed_columns


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


# Orchestrator
def clean_records(header, rows, output, null_columns_log, missing_title_log):
    """Clean the rows, write the CSV and the logs. Return a summary dict."""
    csv.field_size_limit(FIELD_SIZE_LIMIT)

    cleaned_rows, missing_titles = clean_rows(header, rows)
    clean_header, final_rows, removed_columns = drop_empty_columns(header, cleaned_rows)

    write_csv(output, clean_header, final_rows)
    write_log(null_columns_log, "Removed columns", removed_columns)
    write_log(missing_title_log, "Rows without dc.title", missing_titles)

    return {
        "rows": len(final_rows),
        "input_columns": len(header),
        "output_columns": len(clean_header),
        "removed_columns": len(removed_columns),
        "missing_titles": len(missing_titles),
    }
