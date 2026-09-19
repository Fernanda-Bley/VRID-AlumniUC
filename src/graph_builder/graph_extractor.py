"""
Módulo de Extracción y Construcción del Grafo de Conocimiento (VRID-AlumniUC).
Ubicación: src/graph_builder/graph_extractor.py
"""

import pandas as pd
from collections import defaultdict
import itertools
from author_linkage import parse_autoruc_block


def extract_graph_elements(df: pd.DataFrame) -> dict:
    """
    Extrae nodos y relaciones del DataFrame limpio de SIPA.
    
    Retorna un diccionario con DataFrames de Nodos y Aristas:
    - Nodos: Work, Person, Department, Dewey, ODS, Publisher
    - Aristas: AUTHORED, AFFILIATED_TO, CO_AUTHORED_WITH, CLASSIFIED_IN, CONTRIBUTES_TO, PUBLISHED_IN, INTERDEPARTMENTAL
    """
    df = df.copy()

    # Storage for Nodes
    nodes_work = []
    nodes_person = {}      # person_id -> {name, codpers, orcid, is_uc}
    nodes_dept = {}        # dept_name -> {dept_id, name}
    nodes_dewey = {}       # clean_code -> {code, name}
    nodes_ods = {}         # ods_code -> {code, name_en, name_es}
    nodes_publisher = {}   # publisher_name -> {publisher_id, name}

    # Storage for Edges
    edges_authored = []              # (person_id, work_id)
    edges_affiliated = set()         # (person_id, dept_id)
    coauthorship_counts = defaultdict(int) # tuple(sorted(p1, p2)) -> weight
    edges_classified_in = []         # (work_id, dewey_code)
    edges_addresses_ods = []         # (work_id, ods_code)
    edges_published_in = []          # (work_id, publisher_id)
    interdept_counts = defaultdict(int) # tuple(sorted(d1, d2)) -> weight

    dept_counter = 1
    publisher_counter = 1

    for idx, row in df.iterrows():
        work_id = str(row.get("id") or f"WORK_{idx}").strip()
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

        # 1. Extracción de Autores y Afiliaciones desde dc.information.autoruc
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

        # 2. Extracción de Autores secundarios desde dc.contributor.author si no estaban en autoruc
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

        # Red de Co-autoría (Pares únicos de autores por publicación, cap en 30 para evitar explosión O(N^2) en mega-artículos)
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

    # Convert to DataFrames
    df_nodes_work = pd.DataFrame(nodes_work)
    df_nodes_person = pd.DataFrame(list(nodes_person.values()))
    df_nodes_dept = pd.DataFrame(list(nodes_dept.values()))
    df_nodes_dewey = pd.DataFrame(list(nodes_dewey.values()))
    df_nodes_ods = pd.DataFrame(list(nodes_ods.values()))
    df_nodes_publisher = pd.DataFrame(list(nodes_publisher.values()))

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

    return {
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
