"""
Módulo de Formateo y Generación de Scripts para Neo4j (VRID-AlumniUC).
Ubicación: src/graph_builder/neo4j_formatter.py
"""

import os
import pandas as pd


def prepare_neo4j_headers_and_files(graph_dict: dict, output_dir: str):
    """
    Formatea las tablas del grafo con encabezados estándar de Neo4j para importación ultra rápida.
    Genera además el script Cypher import_to_neo4j.cypher con índices y consultas de carga.
    """
    os.makedirs(output_dir, exist_ok=True)
    neo4j_admin_dir = os.path.join(output_dir, "admin_import")
    cypher_dir = os.path.join(output_dir, "cypher_import")
    os.makedirs(neo4j_admin_dir, exist_ok=True)
    os.makedirs(cypher_dir, exist_ok=True)

    # 1. Exportar CSVs para LOAD CSV de Cypher (Estándar)
    cypher_files = {}
    for name, df in graph_dict.items():
        out_file = os.path.join(cypher_dir, f"{name}.csv")
        df.to_csv(out_file, index=False, encoding="utf-8")
        cypher_files[name] = out_file

    # 2. Exportar CSVs con encabezados de neo4j-admin bulk import (:ID, :LABEL, :START_ID, :END_ID, :TYPE)
    admin_mappings = {
        "nodes_work": (["work_id:ID(Work)", "title", "issued_year:INT", "doi", "rights"], "Work"),
        "nodes_person": (["person_id:ID(Person)", "name", "codpers", "orcid", "is_uc:BOOLEAN"], "Person"),
        "nodes_department": (["dept_id:ID(Department)", "name"], "Department"),
        "nodes_dewey": (["dewey_code:ID(Dewey)", "name_es"], "Dewey"),
        "nodes_ods": (["ods_code:ID(ODS)", "name_en", "name_es"], "ODS"),
        "nodes_publisher": (["publisher_id:ID(Publisher)", "name"], "Publisher"),
        "nodes_funder": (["funder_id:ID(Funder)", "name"], "Funder"),
        "nodes_doctype": (["type_id:ID(Doctype)", "name"], "Doctype"),
        "nodes_source": (["source_id:ID(Source)", "name"], "Source"),
        "nodes_keyword": (["keyword_id:ID(Keyword)", "name"], "Keyword"),

        "edges_authored": (["person_id:START_ID(Person)", "work_id:END_ID(Work)"], "AUTHORED"),
        "edges_affiliated": (["person_id:START_ID(Person)", "dept_id:END_ID(Department)"], "AFFILIATED_TO"),
        "edges_coauthored": (["person1_id:START_ID(Person)", "person2_id:END_ID(Person)", "weight:INT"], "CO_AUTHORED_WITH"),
        "edges_classified": (["work_id:START_ID(Work)", "dewey_code:END_ID(Dewey)"], "CLASSIFIED_IN"),
        "edges_ods": (["work_id:START_ID(Work)", "ods_code:END_ID(ODS)"], "CONTRIBUTES_TO_ODS"),
        "edges_published": (["work_id:START_ID(Work)", "publisher_id:END_ID(Publisher)"], "PUBLISHED_IN"),
        "edges_interdepartmental": (["dept1_id:START_ID(Department)", "dept2_id:END_ID(Department)", "weight:INT"], "COLLABORATES_WITH"),
        "edges_funded_by": (["work_id:START_ID(Work)", "funder_id:END_ID(Funder)"], "FUNDED_BY"),
        "edges_has_type": (["work_id:START_ID(Work)", "type_id:END_ID(Doctype)"], "HAS_TYPE"),
        "edges_indexed_in": (["work_id:START_ID(Work)", "source_id:END_ID(Source)"], "INDEXED_IN"),
        "edges_has_keyword": (["work_id:START_ID(Work)", "keyword_id:END_ID(Keyword)"], "HAS_KEYWORD"),
    }

    for name, df in graph_dict.items():
        if name in admin_mappings:
            cols, label_or_type = admin_mappings[name]
            df_admin = df.copy()
            if len(cols) == len(df_admin.columns):
                df_admin.columns = cols
            
            # Formatear booleanos en minúscula para Neo4j (true/false)
            for col in df_admin.columns:
                if ":BOOLEAN" in col:
                    df_admin[col] = df_admin[col].astype(str).str.lower()

            out_admin_file = os.path.join(neo4j_admin_dir, f"{name}.csv")
            df_admin.to_csv(out_admin_file, index=False, encoding="utf-8")

    # 3. Generar Script de Cypher para Carga Directa (import_to_neo4j.cypher)
    cypher_script_path = os.path.join(output_dir, "import_to_neo4j.cypher")
    _generate_cypher_script(cypher_script_path)

    # 4. Generar Script de neo4j-admin import para Bulk Import
    admin_batch_path = os.path.join(output_dir, "neo4j_admin_import.bat")
    _generate_admin_batch_script(admin_batch_path)

    return {
        "cypher_dir": cypher_dir,
        "admin_dir": neo4j_admin_dir,
        "cypher_script": cypher_script_path,
        "admin_batch": admin_batch_path
    }


def _generate_cypher_script(filepath: str):
    cypher = """// ====================================================================
// SCRIPT DE IMPORTACIÓN Y ANÁLISIS EN NEO4J (VRID-AlumniUC)
// ====================================================================

// --- PASO 1: CREAR CONSTRAINTS E ÍNDICES PARA ALTO RENDIMIENTO ---
CREATE CONSTRAINT work_id_unique IF NOT EXISTS FOR (w:Work) REQUIRE w.work_id IS UNIQUE;
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.person_id IS UNIQUE;
CREATE CONSTRAINT dept_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.dept_id IS UNIQUE;
CREATE CONSTRAINT dewey_code_unique IF NOT EXISTS FOR (dw:Dewey) REQUIRE dw.dewey_code IS UNIQUE;
CREATE CONSTRAINT ods_code_unique IF NOT EXISTS FOR (o:ODS) REQUIRE o.ods_code IS UNIQUE;
CREATE CONSTRAINT pub_id_unique IF NOT EXISTS FOR (pub:Publisher) REQUIRE pub.publisher_id IS UNIQUE;
CREATE CONSTRAINT funder_id_unique IF NOT EXISTS FOR (f:Funder) REQUIRE f.funder_id IS UNIQUE;
CREATE CONSTRAINT type_id_unique IF NOT EXISTS FOR (t:Doctype) REQUIRE t.type_id IS UNIQUE;
CREATE CONSTRAINT src_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.source_id IS UNIQUE;
CREATE CONSTRAINT kw_id_unique IF NOT EXISTS FOR (k:Keyword) REQUIRE k.keyword_id IS UNIQUE;

// --- PASO 2: CARGAR NODOS BASE (LOAD CSV) ---
LOAD CSV WITH HEADERS FROM 'file:///nodes_work.csv' AS row
MERGE (w:Work {work_id: row.work_id})
ON CREATE SET w.title = row.title, w.issued_year = toInteger(row.issued_year), w.doi = row.doi, w.rights = row.rights;

LOAD CSV WITH HEADERS FROM 'file:///nodes_person.csv' AS row
MERGE (p:Person {person_id: row.person_id})
ON CREATE SET p.name = row.name, p.codpers = row.codpers, p.orcid = row.orcid, p.is_uc = toBoolean(row.is_uc);

LOAD CSV WITH HEADERS FROM 'file:///nodes_department.csv' AS row
MERGE (d:Department {dept_id: row.dept_id})
ON CREATE SET d.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///nodes_dewey.csv' AS row
MERGE (dw:Dewey {dewey_code: row.dewey_code})
ON CREATE SET dw.name_es = row.name_es;

LOAD CSV WITH HEADERS FROM 'file:///nodes_ods.csv' AS row
MERGE (o:ODS {ods_code: row.ods_code})
ON CREATE SET o.name_en = row.name_en, o.name_es = row.name_es;

LOAD CSV WITH HEADERS FROM 'file:///nodes_publisher.csv' AS row
MERGE (pub:Publisher {publisher_id: row.publisher_id})
ON CREATE SET pub.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///nodes_funder.csv' AS row
MERGE (f:Funder {funder_id: row.funder_id})
ON CREATE SET f.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///nodes_doctype.csv' AS row
MERGE (t:Doctype {type_id: row.type_id})
ON CREATE SET t.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///nodes_source.csv' AS row
MERGE (s:Source {source_id: row.source_id})
ON CREATE SET s.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///nodes_keyword.csv' AS row
MERGE (k:Keyword {keyword_id: row.keyword_id})
ON CREATE SET k.name = row.name;


// --- PASO 3: CARGAR RELACIONES (EDGES) ---
LOAD CSV WITH HEADERS FROM 'file:///edges_authored.csv' AS row
MATCH (p:Person {person_id: row.person_id}), (w:Work {work_id: row.work_id})
MERGE (p)-[:AUTHORED]->(w);

LOAD CSV WITH HEADERS FROM 'file:///edges_affiliated.csv' AS row
MATCH (p:Person {person_id: row.person_id}), (d:Department {dept_id: row.dept_id})
MERGE (p)-[:AFFILIATED_TO]->(d);

LOAD CSV WITH HEADERS FROM 'file:///edges_coauthored.csv' AS row
MATCH (p1:Person {person_id: row.person1_id}), (p2:Person {person_id: row.person2_id})
MERGE (p1)-[r:CO_AUTHORED_WITH]->(p2)
ON CREATE SET r.weight = toInteger(row.weight);

LOAD CSV WITH HEADERS FROM 'file:///edges_classified.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (dw:Dewey {dewey_code: row.dewey_code})
MERGE (w)-[:CLASSIFIED_IN]->(dw);

LOAD CSV WITH HEADERS FROM 'file:///edges_ods.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (o:ODS {ods_code: row.ods_code})
MERGE (w)-[:CONTRIBUTES_TO_ODS]->(o);

LOAD CSV WITH HEADERS FROM 'file:///edges_published.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (pub:Publisher {publisher_id: row.publisher_id})
MERGE (w)-[:PUBLISHED_IN]->(pub);

LOAD CSV WITH HEADERS FROM 'file:///edges_interdepartmental.csv' AS row
MATCH (d1:Department {dept_id: row.dept1_id}), (d2:Department {dept_id: row.dept2_id})
MERGE (d1)-[r:COLLABORATES_WITH]->(d2)
ON CREATE SET r.weight = toInteger(row.weight);

LOAD CSV WITH HEADERS FROM 'file:///edges_funded_by.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (f:Funder {funder_id: row.funder_id})
MERGE (w)-[:FUNDED_BY]->(f);

LOAD CSV WITH HEADERS FROM 'file:///edges_has_type.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (t:Doctype {type_id: row.type_id})
MERGE (w)-[:HAS_TYPE]->(t);

LOAD CSV WITH HEADERS FROM 'file:///edges_indexed_in.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (s:Source {source_id: row.source_id})
MERGE (w)-[:INDEXED_IN]->(s);

LOAD CSV WITH HEADERS FROM 'file:///edges_has_keyword.csv' AS row
MATCH (w:Work {work_id: row.work_id}), (k:Keyword {keyword_id: row.keyword_id})
MERGE (w)-[:HAS_KEYWORD]->(k);


// ====================================================================
// EJEMPLOS DE CONSULTAS ESTRATÉGICAS EN NEO4J
// ====================================================================

// 1. Top 10 Investigadores con mayor red de co-autorías
// MATCH (p:Person)-[r:CO_AUTHORED_WITH]-(co:Person)
// RETURN p.name AS Investigador, count(co) AS Coautores_Unicos, sum(r.weight) AS Colaboraciones_Totales
// ORDER BY Colaboraciones_Totales DESC LIMIT 10;

// 2. Colaboración Interdepartamental entre Facultades UC
// MATCH (d1:Department)-[r:COLLABORATES_WITH]-(d2:Department)
// RETURN d1.name AS Facultad_1, d2.name AS Facultad_2, r.weight AS Obras_Conjuntas
// ORDER BY Obras_Conjuntas DESC LIMIT 15;

// 3. Producción científica por ODS y Unidad Académica
// MATCH (d:Department)<-[:AFFILIATED_TO]-(p:Person)-[:AUTHORED]->(w:Work)-[:CONTRIBUTES_TO_ODS]->(o:ODS)
// RETURN d.name AS Facultad, o.name_es AS ODS, count(DISTINCT w) AS Total_Publicaciones
// ORDER BY Total_Publicaciones DESC LIMIT 20;
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(cypher)


def _generate_admin_batch_script(filepath: str):
    cmd = """@echo off
REM Script de importación masiva ultra rápida con neo4j-admin import
bin\\neo4j-admin database import full ^
  --nodes=Work=data/graph/neo4j/admin_import/nodes_work.csv ^
  --nodes=Person=data/graph/neo4j/admin_import/nodes_person.csv ^
  --nodes=Department=data/graph/neo4j/admin_import/nodes_department.csv ^
  --nodes=Dewey=data/graph/neo4j/admin_import/nodes_dewey.csv ^
  --nodes=ODS=data/graph/neo4j/admin_import/nodes_ods.csv ^
  --nodes=Publisher=data/graph/neo4j/admin_import/nodes_publisher.csv ^
  --nodes=Funder=data/graph/neo4j/admin_import/nodes_funder.csv ^
  --nodes=Doctype=data/graph/neo4j/admin_import/nodes_doctype.csv ^
  --nodes=Source=data/graph/neo4j/admin_import/nodes_source.csv ^
  --nodes=Keyword=data/graph/neo4j/admin_import/nodes_keyword.csv ^
  --relationships=AUTHORED=data/graph/neo4j/admin_import/edges_authored.csv ^
  --relationships=AFFILIATED_TO=data/graph/neo4j/admin_import/edges_affiliated.csv ^
  --relationships=CO_AUTHORED_WITH=data/graph/neo4j/admin_import/edges_coauthored.csv ^
  --relationships=CLASSIFIED_IN=data/graph/neo4j/admin_import/edges_classified.csv ^
  --relationships=CONTRIBUTES_TO_ODS=data/graph/neo4j/admin_import/edges_ods.csv ^
  --relationships=PUBLISHED_IN=data/graph/neo4j/admin_import/edges_published.csv ^
  --relationships=COLLABORATES_WITH=data/graph/neo4j/admin_import/edges_interdepartmental.csv ^
  --relationships=FUNDED_BY=data/graph/neo4j/admin_import/edges_funded_by.csv ^
  --relationships=HAS_TYPE=data/graph/neo4j/admin_import/edges_has_type.csv ^
  --relationships=INDEXED_IN=data/graph/neo4j/admin_import/edges_indexed_in.csv ^
  --relationships=HAS_KEYWORD=data/graph/neo4j/admin_import/edges_has_keyword.csv ^
  --overwrite-destination=true neo4j
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(cmd)
