"""
Script de Limpieza y Normalización Integral para EXPORT_SIPA(in).csv
-------------------------------------------------------------------
1. Reconstruye y alinea las 139.689 filas al esquema oficial de 232 columnas.
2. Rellena los autores faltantes recuperándolos desde dc.information.autoruc y codpers_map.
3. Normaliza las categorías repetidas, códigos Dewey y etiquetas ODS en inglés/español.

Ubicación: scripts/clean_sipa.py
"""

import csv
import os
import sys
import time

# Rutas relativas al proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from author_linkage import build_codpers_map, process_author_linkage
from normalize_categories import normalize_category_columns

ARCHIVO_ORIGEN = os.path.join(BASE_DIR, "data", "EXPORT_SIPA(in).csv")
ARCHIVO_DESTINO = os.path.join(BASE_DIR, "data", "EXPORT_SIPA_clean.csv")
COLUMNAS_VALIDAS = 232

print("=== INICIANDO LIMPIEZA Y NORMALIZACIÓN INTEGRAL DE SIPA ===")
inicio = time.time()
tamano_origen = os.path.getsize(ARCHIVO_ORIGEN)

# PASO 1: Carga y Alineación Estructural en memoria
print("\n[Paso 1/3] Leyendo y alineando filas del CSV origen...")
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

print(f"-> {len(filas_alineadas):,} filas alineadas ({corregidas_estructura:,} filas desbordadas arregladas).")

# PASO 2: Construcción de Catálogo de Autores por ID de Persona (codpers_map)
print("\n[Paso 2/3] Construyendo catálogo global de personas UC (codpers_map)...")
codpers_map = build_codpers_map(encabezado, filas_alineadas)
print(f"-> Catálogo construido con {len(codpers_map):,} personas únicas catalogadas.")

# PASO 3: Recuperación de Autores y Normalización de Categorías/Dewey
print("\n[Paso 3/3] Aplicando recuperación de autores y normalización Dewey/ODS...")
autores_recuperados = 0
filas_procesadas = 0

with open(ARCHIVO_DESTINO, 'w', encoding='utf-8-sig', errors='replace', newline='') as f_out:
    escritor = csv.writer(f_out)
    escritor.writerow(encabezado)

    author_idx = encabezado.index("dc.contributor.author") if "dc.contributor.author" in encabezado else None

    for fila in filas_alineadas:
        filas_procesadas += 1
        tenia_autor = str(fila[author_idx] or "").strip() if author_idx is not None else True

        # 1. Recuperación de Autor Faltante (Nivel 1 codpers + autoruc)
        fila_autores_listos = process_author_linkage(encabezado, fila, codpers_map=codpers_map)
        tiene_autor_nuevo = str(fila_autores_listos[author_idx] or "").strip() if author_idx is not None else True

        if not tenia_autor and tiene_autor_nuevo:
            autores_recuperados += 1

        # 2. Normalización de Categorías, Dewey y ODS
        fila_final = normalize_category_columns(encabezado, fila_autores_listos)
        escritor.writerow(fila_final)

        if filas_procesadas % 30000 == 0:
            print(f"  Procesadas {filas_procesadas:,} / {len(filas_alineadas):,} filas...")

tiempo = time.time() - inicio
tamano_destino = os.path.getsize(ARCHIVO_DESTINO)
ahorro = (1 - tamano_destino / tamano_origen) * 100

print("\n=== LIMPIEZA Y NORMALIZACIÓN FINALIZADA ===")
print(f"Filas procesadas           : {filas_procesadas:,}")
print(f"Estructuras corregidas     : {corregidas_estructura:,}")
print(f"Autores FALTANTES RELLENADOS: {autores_recuperados:,}")
print(f"Personas catalogadas       : {len(codpers_map):,}")
print(f"Archivo generado           : {ARCHIVO_DESTINO}")
print(f"Peso original              : {tamano_origen / 1024 / 1024:.2f} MB")
print(f"Peso final (UTF-8 con BOM) : {tamano_destino / 1024 / 1024:.2f} MB")
print(f"Tiempo total ejecución     : {tiempo:.2f} s")

