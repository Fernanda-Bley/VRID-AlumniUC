"""Run the SIPA document configuration and simple cleanup stages."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from CONFIG import MISSING_TITLES_LOG, NULL_COLUMNS_LOG, OUTPUT, SOURCE
from configure_document import configure_document
from simple_clean import clean_records


if __name__ == "__main__":
    header, rows = configure_document(SOURCE)
    summary = clean_records(header, rows, OUTPUT, NULL_COLUMNS_LOG, MISSING_TITLES_LOG)
    print(summary)
