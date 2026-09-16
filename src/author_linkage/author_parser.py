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


def recover_missing_author(row_dict: dict, codpers_map: dict = None) -> str:
    """
    Intenta recuperar el nombre del autor principal si dc.contributor.author está vacío:
    1. Desde dc.information.autoruc (texto semiestructurado)
    2. Desde dc.contributor.participante o dc.contributor.editor
    3. Mediante el mapa cruzado de sipa.codpersvinculados (ID de persona UC)
    4. Desde dc.publisher / dc.contributor.other (Autor Corporativo/Institucional)
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

    # 4. Recuperar por ID de Persona (sipa.codpersvinculados) en el catálogo de personas
    if codpers_map and row_dict.get("sipa.codpersvinculados"):
        c_ids = [c.strip() for c in str(row_dict["sipa.codpersvinculados"]).split("||") if c.strip()]
        mapped_names = [codpers_map[c_id] for c_id in c_ids if c_id in codpers_map]
        if mapped_names:
            return "||".join(mapped_names)

    # 5. Recuperar Autor Corporativo / Institucional (dc.publisher / dc.contributor.other)
    publisher = str(row_dict.get("dc.publisher", "") or "").strip()
    if publisher:
        # Limpiar trailing dot
        if publisher.endswith("."):
            publisher = publisher[:-1].rstrip()
        return publisher

    other_contrib = str(row_dict.get("dc.contributor.other", "") or "").strip()
    if other_contrib:
        return other_contrib

    return ""


def build_codpers_map(header: list, rows: list) -> dict:
    """
    Construye una tabla hash global de ID Persona UC (codpers) -> Nombre de Autor
    a partir de todas las filas catalogadas del dataset.
    """
    author_idx = header.index("dc.contributor.author") if "dc.contributor.author" in header else None
    codpers_idx = header.index("sipa.codpersvinculados") if "sipa.codpersvinculados" in header else None

    if author_idx is None or codpers_idx is None:
        return {}

    codpers_map = {}
    for row in rows:
        author_val = str(row[author_idx] or "").strip()
        codpers_val = str(row[codpers_idx] or "").strip()

        if author_val and codpers_val:
            authors = [a.strip() for a in author_val.split("||") if a.strip()]
            c_ids = [c.strip() for c in codpers_val.split("||") if c.strip()]

            if len(authors) == len(c_ids):
                for c_id, a_name in zip(c_ids, authors):
                    if c_id and a_name and c_id not in codpers_map:
                        codpers_map[c_id] = a_name

    return codpers_map


def process_author_linkage(header: list, row: list, codpers_map: dict = None) -> list:
    """
    Aplica la recuperación completa de autores desalineados/ausentes a una fila.
    """
    row_copy = list(row)
    row_dict = dict(zip(header, row_copy))

    author_idx = header.index("dc.contributor.author") if "dc.contributor.author" in header else None

    if author_idx is not None and not str(row_copy[author_idx] or "").strip():
        recovered = recover_missing_author(row_dict, codpers_map=codpers_map)
        if recovered:
            row_copy[author_idx] = recovered

    return row_copy

