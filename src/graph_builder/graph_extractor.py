"""
Módulo de Extracción y Construcción del Grafo de Conocimiento (VRID-AlumniUC).
Ubicación: src/graph_builder/graph_extractor.py
"""

import pandas as pd
from collections import defaultdict
import itertools
from author_linkage import parse_autoruc_block


def extract_graph_elements(df: pd.DataFrame, include_extended: bool = True) -> dict:
    """
    Extrae nodos y relaciones del DataFrame limpio de SIPA.
    
    Nodos Núcleo: Work, Person, Department, Dewey, ODS, Publisher
    Nodos Extendidos: Funder, DocumentType, IndexSource, Keyword
    """
    df = df.copy()

    # Core Nodes Storage
    nodes_work = []
    nodes_person = {}      # person_id -> {name, codpers, orcid, is_uc}
    nodes_dept = {}        # dept_name -> {dept_id, name}
    nodes_dewey = {}       # clean_code -> {code, name}
    nodes_ods = {}         # ods_code -> {code, name_en, name_es}
    nodes_publisher = {}   # publisher_name -> {publisher_id, name}

    # Extended Nodes Storage
    nodes_funder = {}      # funder_name -> {funder_id, name}
    nodes_doctype = {}     # type_name -> {type_id, name}
    nodes_source = {}      # source_name -> {source_id, name}
    nodes_keyword = {}     # kw_name -> {keyword_id, name}

    # Core Edges Storage
    edges_authored = []              # (person_id, work_id)
    edges_affiliated = set()         # (person_id, dept_id)
    coauthorship_counts = defaultdict(int) # tuple(sorted(p1, p2)) -> weight
    edges_classified_in = []         # (work_id, dewey_code)
    edges_addresses_ods = []         # (work_id, ods_code)
    edges_published_in = []          # (work_id, publisher_id)
    interdept_counts = defaultdict(int) # tuple(sorted(d1, d2)) -> weight

    # Extended Edges Storage
    edges_funded_by = []             # (work_id, funder_id)
    edges_has_type = []              # (work_id, type_id)
    edges_indexed_in = []            # (work_id, source_id)
    edges_has_keyword = []           # (work_id, keyword_id)

    dept_counter = 1
    publisher_counter = 1
    funder_counter = 1
    type_counter = 1
    source_counter = 1
    kw_counter = 1

    for idx, row in df.iterrows():
        raw_id = str(row.get("id") or "").strip()
        if raw_id and len(raw_id) <= 60 and "||" not in raw_id and " " not in raw_id:
            work_id = raw_id
        else:
            work_id = f"WORK_{idx}"

        title = str(row.get("dc.title") or "").strip()

        issued_date = str(row.get("dc.date.issued") or "").strip()
        issued_year = issued_date[:4] if len(issued_date) >= 4 and issued_date[:4].isdigit() else ""
        doi = str(row.get("dc.identifier.doi") or "").strip()
        rights = str(row.get("dc.rights.spa") or "").strip()

        nodes_work.append({
            "work_id": work_id,
            "title": title,
            "issued_year": issued_year,
            "doi": doi,
            "rights": rights
        })

        # 1. Autores y Afiliaciones desde dc.information.autoruc
        autoruc_str = str(row.get("dc.information.autoruc") or "").strip()
        work_persons = []
        work_depts = set()

        if autoruc_str:
            records = parse_autoruc_block(autoruc_str)
            for r in records:
                a_name = r.get("autor", "").strip()
                c_id = r.get("codpers", "").strip()
                orcid = r.get("orcid", "").strip()
                dept_name = r.get("unidad", "").strip()

                if a_name:
                    p_key = c_id if c_id else f"NAME_{a_name.lower()}"
                    
                    if p_key not in nodes_person:
                        nodes_person[p_key] = {
                            "person_id": p_key,
                            "name": a_name,
                            "codpers": c_id,
                            "orcid": orcid,
                            "is_uc": True if c_id else False
                        }
                    else:
                        if orcid and not nodes_person[p_key]["orcid"]:
                            nodes_person[p_key]["orcid"] = orcid

                    work_persons.append(p_key)
                    edges_authored.append({"person_id": p_key, "work_id": work_id})

                    if dept_name:
                        if dept_name not in nodes_dept:
                            nodes_dept[dept_name] = {
                                "dept_id": f"DEPT_{dept_counter}",
                                "name": dept_name
                            }
                            dept_counter += 1
                        
                        d_id = nodes_dept[dept_name]["dept_id"]
                        edges_affiliated.add((p_key, d_id))
                        work_depts.add(d_id)

        # 2. Autores desde dc.contributor.author
        author_val = str(row.get("dc.contributor.author") or "").strip()
        if author_val:
            authors = [a.strip() for a in author_val.split("||") if a.strip()]
            codpers_val = str(row.get("sipa.codpersvinculados") or "").strip()
            c_ids = [c.strip() for c in codpers_val.split("||") if c.strip()]

            for i, a_name in enumerate(authors):
                c_id = c_ids[i] if i < len(c_ids) else ""
                p_key = c_id if c_id else f"NAME_{a_name.lower()}"

                if p_key not in nodes_person:
                    nodes_person[p_key] = {
                        "person_id": p_key,
                        "name": a_name,
                        "codpers": c_id,
                        "orcid": "",
                        "is_uc": True if c_id else False
                    }
                    work_persons.append(p_key)
                    edges_authored.append({"person_id": p_key, "work_id": work_id})

        # Red de Co-autoría (Cap 30 para evitar O(N^2))
        unique_work_persons = sorted(list(set(work_persons)))
        if len(unique_work_persons) <= 30:
            for p1, p2 in itertools.combinations(unique_work_persons, 2):
                coauthorship_counts[(p1, p2)] += 1

        # Red de Colaboración Interdepartamental
        unique_work_depts = sorted(list(work_depts))
        for d1, d2 in itertools.combinations(unique_work_depts, 2):
            interdept_counts[(d1, d2)] += 1

        # 3. Clasificación Dewey
        ddc_code = str(row.get("dc.subject.ddc") or "").strip()
        dewey_name = str(row.get("dc.subject.dewey[es_ES]") or "").strip()
        if ddc_code:
            if ddc_code not in nodes_dewey:
                nodes_dewey[ddc_code] = {"dewey_code": ddc_code, "name_es": dewey_name}
            edges_classified_in.append({"work_id": work_id, "dewey_code": ddc_code})

        # 4. Objetivos ODS
        ods_en = str(row.get("dc.subject.ods") or "").strip()
        ods_es = str(row.get("dc.subject.odspa") or "").strip()
        if ods_en or ods_es:
            ods_key = ods_en[:2] if ods_en and ods_en[:2].isdigit() else (ods_es[:2] if ods_es and ods_es[:2].isdigit() else ods_en)
            if ods_key:
                if ods_key not in nodes_ods:
                    nodes_ods[ods_key] = {"ods_code": ods_key, "name_en": ods_en, "name_es": ods_es}
                edges_addresses_ods.append({"work_id": work_id, "ods_code": ods_key})

        # 5. Editoriales / Publishers
        publisher_name = str(row.get("dc.publisher") or "").strip()
        if publisher_name:
            if publisher_name not in nodes_publisher:
                nodes_publisher[publisher_name] = {
                    "publisher_id": f"PUB_{publisher_counter}",
                    "name": publisher_name
                }
                publisher_counter += 1
            pub_id = nodes_publisher[publisher_name]["publisher_id"]
            edges_published_in.append({"work_id": work_id, "publisher_id": pub_id})

        # 6. EXTENDIDO: Agencias de Financiamiento (dc.description.funder)
        if include_extended:
            funder_str = str(row.get("dc.description.funder") or "").strip()
            if funder_str:
                funders = [f.strip() for f in funder_str.split("||") if f.strip()]
                for f_name in funders:
                    if f_name not in nodes_funder:
                        nodes_funder[f_name] = {
                            "funder_id": f"FUNDER_{funder_counter}",
                            "name": f_name
                        }
                        funder_counter += 1
                    f_id = nodes_funder[f_name]["funder_id"]
                    edges_funded_by.append({"work_id": work_id, "funder_id": f_id})

            # 7. EXTENDIDO: Tipo de Documento (dc.type)
            doc_type = str(row.get("dc.type") or "").strip()
            if doc_type:
                if doc_type not in nodes_doctype:
                    nodes_doctype[doc_type] = {
                        "type_id": f"TYPE_{type_counter}",
                        "name": doc_type
                    }
                    type_counter += 1
                t_id = nodes_doctype[doc_type]["type_id"]
                edges_has_type.append({"work_id": work_id, "type_id": t_id})

            # 8. EXTENDIDO: Fuente de Indexación (sipa.index / dc.fuente.origen)
            idx_source = str(row.get("sipa.index") or row.get("dc.fuente.origen") or "").strip()
            if idx_source:
                sources = [s.strip() for s in idx_source.split("||") if s.strip()]
                for s_name in sources:
                    if s_name not in nodes_source:
                        nodes_source[s_name] = {
                            "source_id": f"SRC_{source_counter}",
                            "name": s_name
                        }
                        source_counter += 1
                    src_id = nodes_source[s_name]["source_id"]
                    edges_indexed_in.append({"work_id": work_id, "source_id": src_id})

            # 9. EXTENDIDO: Palabras Clave / Temas (dc.subject[es_ES])
            kw_str = str(row.get("dc.subject[es_ES]") or "").strip()
            if kw_str:
                keywords = [k.strip() for k in kw_str.split("||") if k.strip()]
                for kw_name in keywords[:10]: # Limitar a 10 materias por obra
                    if kw_name not in nodes_keyword:
                        nodes_keyword[kw_name] = {
                            "keyword_id": f"KW_{kw_counter}",
                            "name": kw_name
                        }
                        kw_counter += 1
                    k_id = nodes_keyword[kw_name]["keyword_id"]
                    edges_has_keyword.append({"work_id": work_id, "keyword_id": k_id})

    # DataFrames de Nodos
    df_nodes_work = pd.DataFrame(nodes_work)
    df_nodes_person = pd.DataFrame(list(nodes_person.values()))
    df_nodes_dept = pd.DataFrame(list(nodes_dept.values()))
    df_nodes_dewey = pd.DataFrame(list(nodes_dewey.values()))
    df_nodes_ods = pd.DataFrame(list(nodes_ods.values()))
    df_nodes_publisher = pd.DataFrame(list(nodes_publisher.values()))

    # DataFrames de Aristas
    df_edges_authored = pd.DataFrame(edges_authored).drop_duplicates()
    df_edges_affiliated = pd.DataFrame([{"person_id": p, "dept_id": d} for p, d in edges_affiliated])
    df_edges_coauthored = pd.DataFrame([
        {"person1_id": p1, "person2_id": p2, "weight": w}
        for (p1, p2), w in coauthorship_counts.items()
    ])
    df_edges_classified = pd.DataFrame(edges_classified_in).drop_duplicates()
    df_edges_ods = pd.DataFrame(edges_addresses_ods).drop_duplicates()
    df_edges_published = pd.DataFrame(edges_published_in).drop_duplicates()
    df_edges_interdept = pd.DataFrame([
        {"dept1_id": d1, "dept2_id": d2, "weight": w}
        for (d1, d2), w in interdept_counts.items()
    ])

    result = {
        "nodes_work": df_nodes_work,
        "nodes_person": df_nodes_person,
        "nodes_department": df_nodes_dept,
        "nodes_dewey": df_nodes_dewey,
        "nodes_ods": df_nodes_ods,
        "nodes_publisher": df_nodes_publisher,
        "edges_authored": df_edges_authored,
        "edges_affiliated": df_edges_affiliated,
        "edges_coauthored": df_edges_coauthored,
        "edges_classified": df_edges_classified,
        "edges_ods": df_edges_ods,
        "edges_published": df_edges_published,
        "edges_interdepartmental": df_edges_interdept,
    }

    if include_extended:
        result.update({
            "nodes_funder": pd.DataFrame(list(nodes_funder.values())),
            "nodes_doctype": pd.DataFrame(list(nodes_doctype.values())),
            "nodes_source": pd.DataFrame(list(nodes_source.values())),
            "nodes_keyword": pd.DataFrame(list(nodes_keyword.values())),
            "edges_funded_by": pd.DataFrame(edges_funded_by).drop_duplicates(),
            "edges_has_type": pd.DataFrame(edges_has_type).drop_duplicates(),
            "edges_indexed_in": pd.DataFrame(edges_indexed_in).drop_duplicates(),
            "edges_has_keyword": pd.DataFrame(edges_has_keyword).drop_duplicates(),
        })

    return result

