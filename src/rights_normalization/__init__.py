"""
Paquete de normalización de derechos de acceso y permisos.
Ubicación: src/rights_normalization/__init__.py
"""

from .rights_normalizer import normalize_rights_cell, normalize_rights_columns, normalize_rights_in_df

__all__ = ["normalize_rights_cell", "normalize_rights_columns", "normalize_rights_in_df"]

