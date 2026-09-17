"""
Módulo de vinculación autor-obra y recuperación de información semiestructurada.
Ubicación: src/author_linkage/__init__.py
"""

from .author_parser import (
    parse_autoruc_block,
    recover_missing_author,
    build_codpers_map,
    build_codpers_map_from_df,
    recover_missing_authors_in_df,
    process_author_linkage,
)

__all__ = [
    "parse_autoruc_block",
    "recover_missing_author",
    "build_codpers_map",
    "build_codpers_map_from_df",
    "recover_missing_authors_in_df",
    "process_author_linkage",
]


