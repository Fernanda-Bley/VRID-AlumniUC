# Pipeline SIPA


## Estructura

- `src/CONFIG.py`: rutas, nombres de archivos, codificación y constantes del pipeline.
- `src/configure_document.py`: recompone filas dobladas usando el esquema original de 232 columnas.
- `src/simple_clean.py`: contiene funciones de limpieza reutilizables.
- `clean_sipa.py`: ejecuta y coordina todo el pipeline.
- `exploratory.ipynb`: análisis de calidad y comparación de IDs.

## Limpieza aplicada

1. Reconstruye las filas partidas y realinea sus columnas originales.
2. Limpia valores vacíos y artefactos de doble codificación en títulos.
3. Deduplica valores delimitados de autores conservando su orden.
4. Completa `dc.title` con un campo alternativo cuando corresponde.
5. Elimina columnas con 99 % o más de valores nulos y registra sus nombres.
6. Elimina filas completamente vacías.
7. Conserva los registros sin título y los registra en un log.
   
   %Importante!! esta es una deduplicación inicial, se modificará cuando se decida el esquema.
   
8. Deduplica registros solo cuando comparten un identificador fuerte normalizado.
9.  Fusiona las filas duplicadas campo a campo para conservar la máxima información.
10. Estandariza autores delimitados en minúsculas y elimina variantes repetidas.

## Ejecución

Desde la raíz del proyecto:

```bash
python clean_sipa.py
```

La entrada es `data/EXPORT_SIPA(in).csv` y la salida es `data/EXPORT_SIPA_clean.csv`.

## Logs

- `data/EXPORT_SIPA_null_columns.log`: todas las columnas eliminadas por tener 99 % o más de valores nulos.
- `data/EXPORT_SIPA_missing_titles.log`: IDs de registros que no tienen `dc.title` después de usar los campos alternativos.
- `data/EXPORT_SIPA_duplicates.log`: registro CSV de cada fusión por identificador, incluyendo las filas completas en JSON.
