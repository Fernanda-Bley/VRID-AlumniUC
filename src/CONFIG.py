"""Configuration for the SIPA cleaning pipeline."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "EXPORT_SIPA(in).csv"
OUTPUT = DATA / "EXPORT_SIPA_clean.csv"
NULL_COLUMNS_LOG = DATA / "EXPORT_SIPA_null_columns.log"
MISSING_TITLES_LOG = DATA / "EXPORT_SIPA_missing_titles.log"
FOLDED_ROWS_LOG = DATA / "EXPORT_SIPA_folded_rows.log"
EXPECTED_COLUMNS = 232
ENCODING = "utf-8-sig"
FIELD_SIZE_LIMIT = 50_000_000
RECORD_START = re.compile(
	r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12},",
	re.IGNORECASE,
)
MOJIBAKE_REPLACEMENTS = {
	"Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
	"Ã±": "ñ", "Ã¼": "ü", "Ã€": "À", "Ã‰": "É", "Ã‘": "Ñ",
	"Â¿": "¿", "Â¡": "¡", "Â«": "«", "Â»": "»", "Â": "",
	"â€™": "’", "â€œ": "“", "â€": "”", "â€“": "–", "â€”": "—",
	"â€¦": "…", "â†’": "→", "âˆš": "√",
	"√°": "á", "√©": "é", "√≠": "í", "√≥": "ó", "√∫": "ú", "√±": "ñ",
}

TITLE_FALLBACK_FIELDS = (
    "dc.title[es_CL]",
    "dc.title[es_ES]",
    "dc.title.alternative[es_ES]",
    "dc.title.alternative",
)
