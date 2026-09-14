"""
Script de Limpieza para EXPORT_SIPA(in).csv
-------------------------------------------------------------------
Alinea las 139.689 filas del dataset a las 232 columnas de encabezado real.
Ubicación: scripts/clean_sipa.py
"""

import csv
import os
import time

# Determinar rutas relativas al proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO_ORIGEN = os.path.join(BASE_DIR, "data", "EXPORT_SIPA(in).csv")
ARCHIVO_DESTINO = os.path.join(BASE_DIR, "data", "EXPORT_SIPA_clean.csv")
COLUMNAS_VALIDAS = 232

print("=== LIMPIEZA ESPECÍFICA DE EXPORT_SIPA(in).csv ===")
inicio = time.time()
tamano_origen = os.path.getsize(ARCHIVO_ORIGEN)

procesadas = 0
corregidas = 0

with open(ARCHIVO_ORIGEN, 'r', encoding='latin-1', errors='replace', newline='') as f_in:
    lector = csv.reader(f_in)
    
    with open(ARCHIVO_DESTINO, 'w', encoding='utf-8-sig', errors='replace', newline='') as f_out:
        escritor = csv.writer(f_out)

        # Encabezado (232 columnas)
        encabezado = next(lector)
        escritor.writerow(encabezado[:COLUMNAS_VALIDAS])
        procesadas += 1

        # Filas de datos
        for fila in lector:
            procesadas += 1

            # Eliminar comas vacías sobrantes al final de la línea
            while fila and fila[-1].strip() == '':
                fila.pop()

            largo = len(fila)

            # Fila normal (232 columnas o menos)
            if largo <= COLUMNAS_VALIDAS:
                fila_limpia = fila[:COLUMNAS_VALIDAS]
            else:
                # Fila desbordada por comas desalineadas en autores
                corregidas += 1
                sobrantes = largo - COLUMNAS_VALIDAS
                inicio_fila = fila[:12]
                texto_autores = ", ".join(fila[12 : 12 + sobrantes + 1])
                final_fila = fila[12 + sobrantes + 1 : largo]
                fila_limpia = inicio_fila + [texto_autores] + final_fila

            escritor.writerow(fila_limpia)

            if procesadas % 25000 == 0:
                print(f"Procesadas {procesadas:,} filas...")

tiempo = time.time() - inicio
tamano_destino = os.path.getsize(ARCHIVO_DESTINO)
ahorro = (1 - tamano_destino / tamano_origen) * 100

print("\n=== LIMPIEZA FINALIZADA ===")
print(f"Filas procesadas : {procesadas:,}")
print(f"Filas corregidas : {corregidas:,}")
print(f"Archivo generado : {ARCHIVO_DESTINO}")
print(f"Peso original    : {tamano_origen / 1024 / 1024:.2f} MB")
print(f"Peso final       : {tamano_destino / 1024 / 1024:.2f} MB")
print(f"Reducción peso   : {ahorro:.2f}%")
print(f"Tiempo total     : {tiempo:.2f} s")
