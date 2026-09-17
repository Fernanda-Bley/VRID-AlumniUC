"""
Módulo de Normalización de Permisos, Derechos y Niveles de Acceso.
Ubicación: src/rights_normalization/rights_normalizer.py
"""

RIGHTS_MAP = {
    "openaccess": "acceso abierto",
    "open access": "acceso abierto",
    "acceso abierto": "acceso abierto",
    "restrictedaccess": "acceso restringido",
    "restricted access": "acceso restringido",
    "acceso restringido": "acceso restringido",
    "embargoedaccess": "acceso embargado",
    "embargoed access": "acceso embargado",
    "acceso embargado": "acceso embargado",
    "registro bibliográfico": "registro bibliográfico",
    "registro bibliografico": "registro bibliográfico",
}


def normalize_rights_cell(rights_str: str, delimiter: str = "||") -> str:
    """
    Normaliza celdas de derechos y niveles de acceso (dc.rights.spa):
    - Limpia diferencias de mayúsculas ("Acceso abierto" -> "acceso abierto")
    - Estandariza inglés a español ("openAccess" -> "acceso abierto")
    - Deduplica elementos repetidos ("acceso restringido||acceso restringido" -> "acceso restringido")
    """
    if not rights_str or not str(rights_str).strip():
        return ""

    tokens = str(rights_str).split(delimiter)
    seen = set()
    cleaned_rights = []

    for token in tokens:
        clean = token.strip().lower()

        # Si se filtró una firma de autor por desalineación de columnas, descartarla
        if "researcherid" in clean or "orcid" in clean or "autor:" in clean:
            continue

        std_right = RIGHTS_MAP.get(clean, clean)

        if std_right and std_right not in seen:
            seen.add(std_right)
            cleaned_rights.append(std_right)

    return delimiter.join(cleaned_rights)


def normalize_rights_columns(header: list, row: list) -> list:
    """
    Aplica la normalización de derechos de acceso a la fila completa.
    """
    row_copy = list(row)
    for idx, name in enumerate(header):
        if "rights.spa" in name.lower() or "rights.access" in name.lower():
            if row_copy[idx]:
                row_copy[idx] = normalize_rights_cell(row_copy[idx])
    return row_copy


import pandas as pd


def normalize_rights_in_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza todas las columnas de derechos/permisos en un DataFrame de Pandas (ej. dc.rights.spa).
    """
    rights_cols = [c for c in df.columns if "rights.spa" in c.lower() or "rights.access" in c.lower()]
    for col in rights_cols:
        df[col] = df[col].fillna("").astype(str).apply(normalize_rights_cell)
    return df

