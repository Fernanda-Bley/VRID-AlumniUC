"""Run the complete SIPA reconstruction, cleaning, and deduplication pipeline."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from CONFIG import (
    DUPLICATES_LOG,
    FIELD_SIZE_LIMIT,
    MISSING_TITLES_LOG,
    NULL_COLUMNS_LOG,
    OUTPUT,
    SOURCE,
)
from configure_document import configure_document
from clean_duplicates import deduplicate_rows
from simple_clean import (
    clean_rows,
    delete_empty_rows,
    drop_empty_columns,
    write_csv,
    write_log,
)


def run_pipeline():
    """Run every pipeline stage and return a summary of the result."""
    csv.field_size_limit(FIELD_SIZE_LIMIT)

    header, rows = configure_document(SOURCE)
    cleaned_rows, missing_titles = clean_rows(header, rows)
    cleaned_rows = delete_empty_rows(cleaned_rows)
    cleaned_rows, duplicate_records = deduplicate_rows(header, cleaned_rows)
    clean_header, final_rows, removed_columns = drop_empty_columns(
        header, cleaned_rows
    )

    write_csv(OUTPUT, clean_header, final_rows)
    write_log(NULL_COLUMNS_LOG, "Removed columns", removed_columns)
    write_log(MISSING_TITLES_LOG, "Rows without dc.title", missing_titles)
    write_csv(
        DUPLICATES_LOG,
        [
            "kept_id",
            "removed_id",
            "method",
            "matched_fields",
            "reason",
            "kept_row",
            "removed_row",
        ],
        duplicate_records,
    )

    return {
        "rows": len(final_rows),
        "input_columns": len(header),
        "output_columns": len(clean_header),
        "removed_columns": len(removed_columns),
        "missing_titles": len(missing_titles),
        "duplicates": len(duplicate_records),
    }


if __name__ == "__main__":
    print(run_pipeline())
