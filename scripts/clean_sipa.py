"""
Script de Limpieza y Normalización Integrada Basado en Pandas (DataFrame Pipeline)
-------------------------------------------------------------------
Procesa EXPORT_SIPA(in).csv en memoria usando Pandas DataFrames y módulos en src/:
- simple_clean (clean_df, drop_empty_columns_df)
- author_linkage (build_codpers_map_from_df, recover_missing_authors_in_df)
- normalize_categories (normalize_categories_in_df)
- language_normalization (normalize_languages_in_df)
- rights_normalization (normalize_rights_in_df)

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

from simple_clean import clean_df
from author_linkage import build_codpers_map_from_df
from configure_document import normalize_row


ARCHIVO_ORIGEN = os.path.join(BASE_DIR, "data", "EXPORT_SIPA(in).csv")
ARCHIVO_DESTINO = os.path.join(BASE_DIR, "data", "EXPORT_SIPA_clean.csv")
COLUMNAS_VALIDAS = 232

print("=== INICIANDO PIPELINE DE LIMPIEZA CON PANDAS (DATAFRAME) ===")
inicio = time.time()
tamano_origen = os.path.getsize(ARCHIVO_ORIGEN)

# PASO 1: Carga y Alineación Estructural en un DataFrame de Pandas
print("\n[Paso 1/4] Cargando, integrando columnas [] y alineando filas a un DataFrame de Pandas...")
filas_alineadas = []

with open(ARCHIVO_ORIGEN, 'r', encoding='utf-8-sig', errors='replace', newline='') as f_in:
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

        fila_limpia = normalize_row(fila_limpia, encabezado)
        filas_alineadas.append(fila_limpia)

# Crear DataFrame de Pandas con las 232 columnas oficiales
df = pd.DataFrame(filas_alineadas, columns=encabezado)
print(f"-> DataFrame de Pandas creado: {len(df):,} filas x {len(df.columns)} columnas.")

# PASO 2: Construcción de Catálogo de Autores con Pandas (codpers_map)
print("\n[Paso 2/4] Construyendo catálogo hash codpers_map con 17.200+ autores UC desde el DataFrame...")
codpers_map = build_codpers_map_from_df(df)
print(f"-> Catálogo codpers_map generado con {len(codpers_map):,} entradas.")

# PASO 3: Transformaciones y Normalizaciones Integradas con Pandas
print("\n[Paso 3/4] Aplicando transformaciones y normalizaciones con Pandas (módulos integrados)...")
missing_authors_mask = df["dc.contributor.author"].isna() | (df["dc.contributor.author"].astype(str).str.strip() == "")
autores_antes = (~missing_authors_mask).sum()

# Ejecutar limpieza integrada usando clean_df de simple_clean.py
df_clean, missing_titles = clean_df(df, codpers_map=codpers_map)

autores_despues = (df_clean["dc.contributor.author"].fillna("").astype(str).str.strip() != "").sum()
autores_recuperados = autores_despues - autores_antes

print(f"-> Autores faltantes recuperados en el DataFrame: {autores_recuperados:,}")
print(f"-> Filas sin título registradas: {len(missing_titles):,}")

# PASO 4: Exportar DataFrame procesado a CSV UTF-8 con BOM
print("\n[Paso 4/4] Guardando el DataFrame normalizado a CSV...")
df_clean.to_csv(ARCHIVO_DESTINO, index=False, encoding="utf-8-sig")

tiempo = time.time() - inicio
tamano_destino = os.path.getsize(ARCHIVO_DESTINO)

print("\n=== PIPELINE DE PANDAS FINALIZADO CON ÉXITO ===")
print(f"Filas procesadas           : {len(df_clean):,}")
print(f"Estructuras corregidas     : {corregidas_estructura:,}")
print(f"Autores FALTANTES RELLENADOS: {autores_recuperados:,}")
print(f"Personas catalogadas       : {len(codpers_map):,}")
print(f"Archivo generado           : {ARCHIVO_DESTINO}")
print(f"Peso original              : {tamano_origen / 1024 / 1024:.2f} MB")
print(f"Peso final (UTF-8 con BOM) : {tamano_destino / 1024 / 1024:.2f} MB")
print(f"Tiempo total ejecución     : {tiempo:.2f} s")

