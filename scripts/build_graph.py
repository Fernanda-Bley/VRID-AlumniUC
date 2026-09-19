"""
Script Principal de Construcción y Exportación del Grafo de Conocimiento (VRID-AlumniUC)
--------------------------------------------------------------------------------
Lee EXPORT_SIPA_clean.csv, extrae las entidades (Nodos) y conexiones (Aristas), 
y exporta los archivos CSV de nodos y relaciones listos para análisis o carga en Neo4j / NetworkX.

Ubicación: scripts/build_graph.py
"""

import os
import sys
import time
import pandas as pd

# Rutas relativas al proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from graph_builder import extract_graph_elements, prepare_neo4j_headers_and_files

ARCHIVO_ORIGEN = os.path.join(BASE_DIR, "data", "EXPORT_SIPA_clean.csv")
DIR_GRAFO = os.path.join(BASE_DIR, "data", "graph")
DIR_NEO4J = os.path.join(BASE_DIR, "data", "graph", "neo4j")

print("=== INICIANDO CONSTRUCCIÓN DEL GRAFO DE CONOCIMIENTO PARA NEO4J (VRID-AlumniUC) ===")
t0 = time.time()

if not os.path.exists(ARCHIVO_ORIGEN):
    raise FileNotFoundError(f"No se encontró el archivo limpio en {ARCHIVO_ORIGEN}. Ejecuta primero scripts/clean_sipa.py")

print(f"\n[1/4] Cargando dataset limpio desde {ARCHIVO_ORIGEN}...")
df = pd.read_csv(ARCHIVO_ORIGEN, low_memory=False)
print(f"-> Cargadas {len(df):,} filas y {len(df.columns)} columnas.")

print("\n[2/4] Extrayendo Nodos y Relaciones del Grafo...")
graph = extract_graph_elements(df, include_extended=True)

os.makedirs(DIR_GRAFO, exist_ok=True)

print("\n[3/4] Guardando tablas CSV del Grafo estándar en data/graph/...")
resumen_nodos = {}
resumen_aristas = {}

for nombre, df_elem in graph.items():
    ruta_out = os.path.join(DIR_GRAFO, f"{nombre}.csv")
    df_elem.to_csv(ruta_out, index=False, encoding="utf-8-sig")
    if nombre.startswith("nodes_"):
        resumen_nodos[nombre.replace("nodes_", "")] = len(df_elem)
    else:
        resumen_aristas[nombre.replace("edges_", "")] = len(df_elem)

print("\n[4/4] Formateando tablas y generando scripts de importación para Neo4j...")
neo4j_info = prepare_neo4j_headers_and_files(graph, DIR_NEO4J)

tiempo = time.time() - t0

print("\n=== RESUMEN DEL GRAFO DE CONOCIMIENTO GENERADO PARA NEO4J ===")
print("\n--- NODOS EXTRAÍDOS ---")
for tipo, cant in resumen_nodos.items():
    print(f"  • Nodo :{tipo.capitalize():<15} : {cant:>10,} elementos")

print("\n--- RELACIONES EXTRAÍDAS ---")
for rel, cant in resumen_aristas.items():
    print(f"  • Relación -[:{rel.upper()}]-> : {cant:>10,} conexiones")

print("\n--- ARCHIVOS PARA NEO4J GENERADOS ---")
print(f"  • Archivos CSV para Cypher (LOAD CSV)  : {neo4j_info['cypher_dir']}")
print(f"  • Archivos CSV para neo4j-admin bulk  : {neo4j_info['admin_dir']}")
print(f"  • Script de Carga y Consultas Cypher  : {neo4j_info['cypher_script']}")
print(f"  • Script de Importación Bulk (.bat)   : {neo4j_info['admin_batch']}")
print(f"\nTiempo total ejecución                : {tiempo:.2f} s")

