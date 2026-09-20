# Pipeline SIPA - Limpieza y Normalización de Datos

Este repositorio contiene el pipeline modular para la limpieza, reparación estructural, recuperación de autores ausentes y normalización del dataset **EXPORT_SIPA**.

---

## 📁 Estructura del Proyecto (`src/` y `scripts/`)

- `scripts/clean_sipa.py`: Script principal ejecutable que corre el pipeline completo en memoria basado en Pandas.
- `src/simple_clean.py`: Orquestador de limpieza base, desduplicación de celdas multivalor y recuperación de títulos por fallback.
- `src/author_linkage/`: Módulo de recuperación Nivel 1 de autores faltantes mediante catálogo hash de personas UC.
- `src/normalize_categories/`: Módulo de normalización de códigos Dewey (DDC), ODS bilingües y materias.
- `src/language_normalization/`: Módulo de estandarización de idiomas a ISO 639-1 (`en`, `es`).
- `src/rights_normalization/`: Módulo de unificación de derechos y permisos de acceso (`acceso abierto`, `acceso restringido`).
- `src/CONFIG.py`: Configuración global, rutas relativas y tabla de mapeo Mojibake.

---

## 🧹 Resumen de Limpiezas y Normalizaciones Aplicadas (Fase Pre-Grafo)

1. **Alineación y Reparación Estructural**:
   - Reconstrucción de **149 filas desalineadas** por saltos de línea internos en resúmenes.
   - Alineación estricta de las 139.688 filas a la estructura oficial de 232 columnas.

2. **Recuperación Nivel 1 de Autores Faltantes**:
   - Se recuperaron **2.851 autores ausentes** (reduciendo las filas sin autor de 3.460 a solo 805).
   - Construcción de un catálogo hash con **17.206 personas UC** cruzando `dc.information.autoruc` y `sipa.codpersvinculados`.

3. **Normalización Disciplinar Dewey (DDC)**:
   - Corrección de comas decimales a puntos (`512,942` $\rightarrow$ `512.942`) y ceros a la izquierda (`70` $\rightarrow$ `070`).
   - Sincronización de códigos numéricos con su descripción en español (`610` $\rightarrow$ `Medicina y salud`, `340` $\rightarrow$ `Derecho`).

4. **Preservación Bilingüe ODS**:
   - Estandarización de etiquetas ODS en inglés para `dc.subject.ods` y en español para `dc.subject.odspa`.

5. **Estandarización de Idiomas y Derechos**:
   - Idiomas a ISO 639-1 (`eng` $\rightarrow$ `en`, `spa` $\rightarrow$ `es`).
   - Permisos de acceso a taxonomía unificada (`openAccess` $\rightarrow$ `acceso abierto`).

---

## 🚀 Ejecución del Pipeline de Limpieza

Desde la raíz del proyecto:

```bash
python scripts/clean_sipa.py
```

- **Entrada**: `data/EXPORT_SIPA(in).csv` (637,49 MB)
- **Salida**: `data/EXPORT_SIPA_clean.csv` (254,41 MB, UTF-8 con BOM)
- **Tiempo de ejecución**: ~82 segundos (139.688 filas x 232 columnas)

---

## 📄 Logs de Auditoría (`data/`)

- `data/EXPORT_SIPA_null_columns.log`: Registro de columnas eliminadas por estar 100% vacías.
- `data/EXPORT_SIPA_missing_titles.log`: Registro de los 1.379 registros sin título tras aplicar fallbacks.
- `docs/REPORTE_CALIDAD_Y_NORMALIZACION_SIPA.md`: Informe formal detallado de métricas y hallazgos.
