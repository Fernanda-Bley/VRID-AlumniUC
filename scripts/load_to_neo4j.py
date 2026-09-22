"""
Script de Carga Directa del Grafo a Neo4j mediante Python Driver (UNWIND Batch Ingestion)
-------------------------------------------------------------------------------------
Conecta a la base de datos local Neo4j (neo4j://127.0.0.1:7687), crea las restricciones/índices
y realiza la ingestión masiva por lotes (batches) de los 576.000+ Nodos y 2.400.000+ Aristas.

Ubicación: scripts/load_to_neo4j.py
"""

import os
import sys
import time
import pandas as pd
from neo4j import GraphDatabase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_GRAFO = os.path.join(BASE_DIR, "data", "graph")

URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "Dmardones12")
BATCH_SIZE = 5000

print("=== INICIANDO INGESTIÓN MASIVA DEL GRAFO A NEO4J ===")
t0 = time.time()


def create_constraints(driver):
    print("\n[1/3] Creando restricciones e índices de unicidad en Neo4j...")
    constraints = [
        "CREATE CONSTRAINT work_id_unique IF NOT EXISTS FOR (w:Work) REQUIRE w.work_id IS UNIQUE",
        "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.person_id IS UNIQUE",
        "CREATE CONSTRAINT dept_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.dept_id IS UNIQUE",
        "CREATE CONSTRAINT dewey_code_unique IF NOT EXISTS FOR (dw:Dewey) REQUIRE dw.dewey_code IS UNIQUE",
        "CREATE CONSTRAINT ods_code_unique IF NOT EXISTS FOR (o:ODS) REQUIRE o.ods_code IS UNIQUE",
        "CREATE CONSTRAINT pub_id_unique IF NOT EXISTS FOR (pub:Publisher) REQUIRE pub.publisher_id IS UNIQUE",
        "CREATE CONSTRAINT funder_id_unique IF NOT EXISTS FOR (f:Funder) REQUIRE f.funder_id IS UNIQUE",
        "CREATE CONSTRAINT type_id_unique IF NOT EXISTS FOR (t:Doctype) REQUIRE t.type_id IS UNIQUE",
        "CREATE CONSTRAINT src_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.source_id IS UNIQUE",
        "CREATE CONSTRAINT kw_id_unique IF NOT EXISTS FOR (k:Keyword) REQUIRE k.keyword_id IS UNIQUE"
    ]
    with driver.session() as session:
        for cypher in constraints:
            session.run(cypher)
    print("-> Restricciones e índices listos.")


def load_batch(driver, query, data_list):
    total = len(data_list)
    for i in range(0, total, BATCH_SIZE):
        batch = data_list[i : i + BATCH_SIZE]
        for attempt in range(3):
            try:
                with driver.session() as session:
                    session.run(query, batch=batch)
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(2)


def load_nodes(driver):
    print("\n[2/3] Cargando Nodos en Neo4j...")
    
    # 1. Work
    df_work = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_work.csv")).fillna("")
    print(f"  • Cargando {len(df_work):,} nodos :Work...")
    q_work = """
    UNWIND $batch AS row
    MERGE (w:Work {work_id: row.work_id})
    ON CREATE SET w.title = row.title, w.issued_year = toInteger(row.issued_year), w.doi = row.doi, w.rights = row.rights
    """
    load_batch(driver, q_work, df_work.to_dict("records"))

    # 2. Person
    df_person = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_person.csv"), low_memory=False).fillna("")
    print(f"  • Cargando {len(df_person):,} nodos :Person...")
    q_person = """
    UNWIND $batch AS row
    MERGE (p:Person {person_id: row.person_id})
    ON CREATE SET p.name = row.name, p.codpers = row.codpers, p.orcid = row.orcid, p.is_uc = toBoolean(row.is_uc)
    """
    load_batch(driver, q_person, df_person.to_dict("records"))

    # 3. Department
    df_dept = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_department.csv")).fillna("")
    print(f"  • Cargando {len(df_dept):,} nodos :Department...")
    q_dept = """
    UNWIND $batch AS row
    MERGE (d:Department {dept_id: row.dept_id})
    ON CREATE SET d.name = row.name
    """
    load_batch(driver, q_dept, df_dept.to_dict("records"))

    # 4. Dewey
    df_dewey = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_dewey.csv")).fillna("")
    print(f"  • Cargando {len(df_dewey):,} nodos :Dewey...")
    q_dewey = """
    UNWIND $batch AS row
    MERGE (dw:Dewey {dewey_code: row.dewey_code})
    ON CREATE SET dw.name_es = row.name_es
    """
    load_batch(driver, q_dewey, df_dewey.to_dict("records"))

    # 5. ODS
    df_ods = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_ods.csv")).fillna("")
    print(f"  • Cargando {len(df_ods):,} nodos :ODS...")
    q_ods = """
    UNWIND $batch AS row
    MERGE (o:ODS {ods_code: row.ods_code})
    ON CREATE SET o.name_en = row.name_en, o.name_es = row.name_es
    """
    load_batch(driver, q_ods, df_ods.to_dict("records"))

    # 6. Publisher
    df_pub = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_publisher.csv")).fillna("")
    print(f"  • Cargando {len(df_pub):,} nodos :Publisher...")
    q_pub = """
    UNWIND $batch AS row
    MERGE (pub:Publisher {publisher_id: row.publisher_id})
    ON CREATE SET pub.name = row.name
    """
    load_batch(driver, q_pub, df_pub.to_dict("records"))

    # 7. Funder
    df_funder = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_funder.csv")).fillna("")
    print(f"  • Cargando {len(df_funder):,} nodos :Funder...")
    q_funder = """
    UNWIND $batch AS row
    MERGE (f:Funder {funder_id: row.funder_id})
    ON CREATE SET f.name = row.name
    """
    load_batch(driver, q_funder, df_funder.to_dict("records"))

    # 8. Doctype
    df_type = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_doctype.csv")).fillna("")
    print(f"  • Cargando {len(df_type):,} nodos :Doctype...")
    q_type = """
    UNWIND $batch AS row
    MERGE (t:Doctype {type_id: row.type_id})
    ON CREATE SET t.name = row.name
    """
    load_batch(driver, q_type, df_type.to_dict("records"))

    # 9. Source
    df_src = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_source.csv")).fillna("")
    print(f"  • Cargando {len(df_src):,} nodos :Source...")
    q_src = """
    UNWIND $batch AS row
    MERGE (s:Source {source_id: row.source_id})
    ON CREATE SET s.name = row.name
    """
    load_batch(driver, q_src, df_src.to_dict("records"))

    # 10. Keyword
    df_kw = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_keyword.csv")).fillna("")
    print(f"  • Cargando {len(df_kw):,} nodos :Keyword...")
    q_kw = """
    UNWIND $batch AS row
    MERGE (k:Keyword {keyword_id: row.keyword_id})
    ON CREATE SET k.name = row.name
    """
    load_batch(driver, q_kw, df_kw.to_dict("records"))


def load_edges(driver):
    print("\n[3/3] Cargando Relaciones en Neo4j...")

    # 1. AUTHORED
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_authored.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:AUTHORED]->...")
    q = """
    UNWIND $batch AS row
    MATCH (p:Person {person_id: row.person_id}), (w:Work {work_id: row.work_id})
    MERGE (p)-[:AUTHORED]->(w)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 2. AFFILIATED_TO
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_affiliated.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:AFFILIATED_TO]->...")
    q = """
    UNWIND $batch AS row
    MATCH (p:Person {person_id: row.person_id}), (d:Department {dept_id: row.dept_id})
    MERGE (p)-[:AFFILIATED_TO]->(d)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 3. CO_AUTHORED_WITH
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_coauthored.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:CO_AUTHORED_WITH]->...")
    q = """
    UNWIND $batch AS row
    MATCH (p1:Person {person_id: row.person1_id}), (p2:Person {person_id: row.person2_id})
    MERGE (p1)-[r:CO_AUTHORED_WITH]->(p2)
    ON CREATE SET r.weight = toInteger(row.weight)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 4. CLASSIFIED_IN
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_classified.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:CLASSIFIED_IN]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (dw:Dewey {dewey_code: row.dewey_code})
    MERGE (w)-[:CLASSIFIED_IN]->(dw)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 5. CONTRIBUTES_TO_ODS
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_ods.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:CONTRIBUTES_TO_ODS]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (o:ODS {ods_code: row.ods_code})
    MERGE (w)-[:CONTRIBUTES_TO_ODS]->(o)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 6. PUBLISHED_IN
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_published.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:PUBLISHED_IN]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (pub:Publisher {publisher_id: row.publisher_id})
    MERGE (w)-[:PUBLISHED_IN]->(pub)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 7. COLLABORATES_WITH (Interdepartmental)
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_interdepartmental.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:COLLABORATES_WITH]->...")
    q = """
    UNWIND $batch AS row
    MATCH (d1:Department {dept_id: row.dept1_id}), (d2:Department {dept_id: row.dept2_id})
    MERGE (d1)-[r:COLLABORATES_WITH]->(d2)
    ON CREATE SET r.weight = toInteger(row.weight)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 8. FUNDED_BY
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_funded_by.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:FUNDED_BY]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (f:Funder {funder_id: row.funder_id})
    MERGE (w)-[:FUNDED_BY]->(f)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 9. HAS_TYPE
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_has_type.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:HAS_TYPE]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (t:Doctype {type_id: row.type_id})
    MERGE (w)-[:HAS_TYPE]->(t)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 10. INDEXED_IN
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_indexed_in.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:INDEXED_IN]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (s:Source {source_id: row.source_id})
    MERGE (w)-[:INDEXED_IN]->(s)
    """
    load_batch(driver, q, df.to_dict("records"))

    # 11. HAS_KEYWORD
    df = pd.read_csv(os.path.join(DIR_GRAFO, "edges_has_keyword.csv")).fillna("")
    print(f"  • Cargando {len(df):,} relaciones -[:HAS_KEYWORD]->...")
    q = """
    UNWIND $batch AS row
    MATCH (w:Work {work_id: row.work_id}), (k:Keyword {keyword_id: row.keyword_id})
    MERGE (w)-[:HAS_KEYWORD]->(k)
    """
    load_batch(driver, q, df.to_dict("records"))


def main():
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        create_constraints(driver)
        load_nodes(driver)
        load_edges(driver)

    tiempo = time.time() - t0
    print(f"\n=== INGESTIÓN COMPLETADA EXITOSAMENTE EN {tiempo:.2f} s ===")

if __name__ == "__main__":
    main()
