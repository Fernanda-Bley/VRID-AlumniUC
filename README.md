# Pipeline SIPA


## Estructura

- `src/CONFIG.py`: rutas, nombres de archivos, codificación y constantes del pipeline.
- `src/configure_document.py`: recompone filas dobladas usando el esquema original de 232 columnas.
- `src/simple_clean.py`: aplica la limpieza simple.
- `clean_sipa.py`: ejecuta el pipeline completo.
- `exploratory.ipynb`: análisis de calidad y comparación de IDs.

## Limpieza aplicada

1. Reconstruye las filas partidas y realinea sus columnas originales.
2. Limpia valores vacíos y artefactos de doble codificación en títulos.
3. Deduplica valores delimitados de autores conservando su orden.
4. Completa `dc.title` con un campo alternativo cuando corresponde.
5. Elimina únicamente columnas con 100 % de valores nulos.
6. Conserva los registros sin título y los registra en un log.

## Ejecución

Desde la raíz del proyecto:

```bash
python clean_sipa.py
```

La entrada es `data/EXPORT_SIPA(in).csv` y la salida es `data/EXPORT_SIPA_clean.csv`.

## Logs

- `data/EXPORT_SIPA_null_columns.log`: columnas eliminadas por estar completamente vacías.
- `data/EXPORT_SIPA_missing_titles.log`: IDs de registros que no tienen `dc.title` después de usar los campos alternativos.
