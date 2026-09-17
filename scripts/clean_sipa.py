"""
Script de Limpieza y Normalización Integrada Basado en Pandas (DataFrame Pipeline)
-------------------------------------------------------------------
Procesa EXPORT_SIPA(in).csv en memoria usando Pandas DataFrames:
1. Reconstrucción y alineación estructural a 232 columnas en un DataFrame.
2. Recuperación de autores faltantes con codpers_map y vectorización de Pandas.
3. Normalización de categorías, códigos Dewey, ODS, idiomas ISO y derechos de acceso.

Ubicación: scripts/clean_sipa.py
"""

import csv
import os
import sys
import time
import pandas as pd

# Rutas relativas al proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from author_linkage import build_codpers_map, recover_missing_author
from normalize_categories import (
    normalize_category_columns,
    normalize_dewey_pair,
    normalize_ods_tag,
)
from language_normalization import normalize_language_code
from rights_normalization import normalize_rights_cell

ARCHIVO_ORIGEN = os.path.join(BASE_DIR, "data", "EXPORT_SIPA(in).csv")
ARCHIVO_DESTINO = os.path.join(BASE_DIR, "data", "EXPORT_SIPA_clean.csv")
COLUMNAS_VALIDAS = 232

print("=== INICIANDO PIPELINE DE LIMPIEZA CON PANDAS (DATAFRAME) ===")
inicio = time.time()
tamano_origen = os.path.getsize(ARCHIVO_ORIGEN)

# PASO 1: Carga y Alineación Estructural en un DataFrame de Pandas
print("\n[Paso 1/4] Cargando y alineando filas del CSV origen a un DataFrame de Pandas...")
filas_alineadas = []

with open(ARCHIVO_ORIGEN, 'r', encoding='latin-1', errors='replace', newline='') as f_in:
    lector = csv.reader(f_in)
    encabezado = next(lector)[:COLUMNAS_VALIDAS]

    corregidas_estructura = 0
    for fila in lector:
        while fila and fila[-1].strip() == '':
            fila.pop()

        largo = len(fila)
        if largo <= COLUMNAS_VALIDAS:
            fila_limpia = fila[:COLUMNAS_VALIDAS]
            fila_limpia.extend([""] * (COLUMNAS_VALIDAS - len(fila_limpia)))
        else:
            corregidas_estructura += 1
            sobrantes = largo - COLUMNAS_VALIDAS
            inicio_fila = fila[:12]
            texto_autores = ", ".join(fila[12 : 12 + sobrantes + 1])
            final_fila = fila[12 + sobrantes + 1 : largo]
            fila_limpia = inicio_fila + [texto_autores] + final_fila
            fila_limpia.extend([""] * (COLUMNAS_VALIDAS - len(fila_limpia)))

        filas_alineadas.append(fila_limpia)

# Crear DataFrame de Pandas con las 232 columnas oficiales
df = pd.DataFrame(filas_alineadas, columns=encabezado)
print(f"-> DataFrame de Pandas creado: {len(df):,} filas x {len(df.columns)} columnas.")

# PASO 2: Construcción de Catálogo de Autores (codpers_map)
print("\n[Paso 2/4] Construyendo catálogo hash codpers_map con 17.200+ autores UC...")
codpers_map = build_codpers_map(encabezado, filas_alineadas)
print(f"-> Catálogo codpers_map generado con {len(codpers_map):,} entradas.")

# PASO 3: Transformaciones y Normalización Vectorizada con Pandas
print("\n[Paso 3/4] Aplicando transformaciones y normalizaciones con Pandas...")

# A. Recuperación de Autores Faltantes con Pandas
missing_authors_mask = df["dc.contributor.author"].isna() | (df["dc.contributor.author"].astype(str).str.strip() == "")
autores_antes = (~missing_authors_mask).sum()

def pandas_recover_author(row):
    return recover_missing_author(row.to_dict(), codpers_map=codpers_map)

df.loc[missing_authors_mask, "dc.contributor.author"] = df[missing_authors_mask].apply(pandas_recover_author, axis=1)
autores_despues = (df["dc.contributor.author"].fillna("").astype(str).str.strip() != "").sum()
autores_recuperados = autores_despues - autores_antes
print(f"-> Autores faltantes recuperados en el DataFrame: {autores_recuperados:,}")

# B. Normalización Dewey (DDC) con Pandas
print("-> Normalizando códigos Dewey con Pandas...")
dewey_results = df.apply(lambda r: normalize_dewey_pair(r.get("dc.subject.ddc"), r.get("dc.subject.dewey[es_ES]")), axis=1)
df["dc.subject.ddc"] = [r[0] for r in dewey_results]
df["dc.subject.dewey[es_ES]"] = [r[1] for r in dewey_results]

# C. Normalización ODS (Inglés en dc.subject.ods, Español en dc.subject.odspa) con Pandas
print("-> Normalizando etiquetas ODS bilingües con Pandas...")
df["dc.subject.ods"] = df["dc.subject.ods"].fillna("").astype(str).apply(lambda x: normalize_ods_tag(x, target_lang="en"))
df["dc.subject.odspa"] = df["dc.subject.odspa"].fillna("").astype(str).apply(lambda x: normalize_ods_tag(x, target_lang="es"))

# D. Normalización de Idiomas ISO (639-1) con Pandas
print("-> Estandarizando idiomas ISO con Pandas...")
df["dc.language.iso"] = df["dc.language.iso"].fillna("").astype(str).apply(normalize_language_code)

# E. Normalización de Derechos de Acceso con Pandas
print("-> Unificando derechos de acceso con Pandas...")
df["dc.rights.spa"] = df["dc.rights.spa"].fillna("").astype(str).apply(normalize_rights_cell)

# PASO 4: Exportar DataFrame procesado a CSV UTF-8 con BOM
print("\n[Paso 4/4] Guardando el DataFrame normalizado a CSV...")
df.to_csv(ARCHIVO_DESTINO, index=False, encoding="utf-8-sig")

tiempo = time.time() - inicio
tamano_destino = os.path.getsize(ARCHIVO_DESTINO)

print("\n=== PIPELINE DE PANDAS FINALIZADO CON ÉXITO ===")
print(f"Filas procesadas           : {len(df):,}")
print(f"Estructuras corregidas     : {corregidas_estructura:,}")
print(f"Autores FALTANTES RELLENADOS: {autores_recuperados:,}")
print(f"Personas catalogadas       : {len(codpers_map):,}")
print(f"Archivo generado           : {ARCHIVO_DESTINO}")
print(f"Peso original              : {tamano_origen / 1024 / 1024:.2f} MB")
print(f"Peso final (UTF-8 con BOM) : {tamano_destino / 1024 / 1024:.2f} MB")
print(f"Tiempo total ejecución     : {tiempo:.2f} s")
