"""
Parser de texto semiestructurado de autoría y recuperación de autores ausentes.
Ubicación: src/author_linkage/author_parser.py
"""


def parse_autoruc_block(autoruc_text: str) -> list:
    """
    Parsea el campo semiestructurado dc.information.autoruc.
    Ejemplo de entrada:
        "Instituto de Física; Diaz Gutierrez, Marco Aurelio; 0000-0001-7376-5555; 104746 || Facultad de Matemáticas; Garay Walls, Francisca Montserrat; S/I; 131813"
    
    Retorna una lista de diccionarios con los atributos extraídos:
        [
            {"unidad": "Instituto de Física", "autor": "Diaz Gutierrez, Marco Aurelio", "orcid": "0000-0001-7376-5555", "codpers": "104746"},
            ...
        ]
    """
    if not autoruc_text or not str(autoruc_text).strip():
        return []

    parsed_records = []
    blocks = str(autoruc_text).split("||")

    for block in blocks:
        parts = [p.strip() for p in block.split(";")]
        if len(parts) >= 2:
            unidad = parts[0] if parts[0] and parts[0] != "S/I" else ""
            autor = parts[1] if parts[1] and parts[1] != "S/I" else ""
            orcid = parts[2] if len(parts) > 2 and parts[2] and parts[2] != "S/I" else ""
            codpers = parts[3] if len(parts) > 3 and parts[3] and parts[3] != "S/I" else ""

            if autor:
                parsed_records.append({
                    "unidad": unidad,
                    "autor": autor,
                    "orcid": orcid,
                    "codpers": codpers,
                })

    return parsed_records


def recover_missing_author(row_dict: dict) -> str:
    """
    Intenta recuperar el nombre del autor principal si dc.contributor.author está vacío,
    buscando en orden en dc.information.autoruc, dc.contributor.participante y dc.contributor.editor.
    """
    current_author = str(row_dict.get("dc.contributor.author", "") or "").strip()
    if current_author:
        return current_author

    # 1. Recuperar desde dc.information.autoruc
    autoruc = str(row_dict.get("dc.information.autoruc", "") or "").strip()
    if autoruc:
        records = parse_autoruc_block(autoruc)
        authors = [r["autor"] for r in records if r.get("autor")]
        if authors:
            return "||".join(authors)

    # 2. Recuperar desde dc.contributor.participante
    participante = str(row_dict.get("dc.contributor.participante", "") or "").strip()
    if participante:
        return participante

    # 3. Recuperar desde dc.contributor.editor
    editor = str(row_dict.get("dc.contributor.editor", "") or "").strip()
    if editor:
        return editor

    return ""


def process_author_linkage(header: list, row: list) -> list:
    """
    Aplica la recuperación de autores desalineados/ausentes a una fila completa.
    """
    row_copy = list(row)
    row_dict = dict(zip(header, row_copy))

    author_idx = header.index("dc.contributor.author") if "dc.contributor.author" in header else None

    if author_idx is not None and not str(row_copy[author_idx] or "").strip():
        recovered = recover_missing_author(row_dict)
        if recovered:
            row_copy[author_idx] = recovered

    return row_copy
