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
    return value in {"#�NOMBRE?", "#NOMBRE?", "#�VALOR!", "#VALOR!"}


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


def clean_rows(header, rows):
    """Clean all rows and detect which ones ended up without a title.

    Returns (cleaned_rows, missing_title_ids).
    """
    author_indexes = find_author_indexes(header)
    title_index = find_title_index(header)

    cleaned_rows = []
    missing_titles = []

    for row in rows:
        cleaned = clean_row(row, header, author_indexes, title_index)
        if has_missing_title(cleaned, title_index):
            missing_titles.append(row[0])
        cleaned_rows.append(cleaned)

    return cleaned_rows, missing_titles


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


