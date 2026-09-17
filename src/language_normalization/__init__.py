"""
Paquete de estandarización de idiomas ISO.
Ubicación: src/language_normalization/__init__.py
"""

from .language_normalizer import normalize_language_code, normalize_language_columns

__all__ = ["normalize_language_code", "normalize_language_columns"]
