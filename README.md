![Portada](scr/Grupo-11-Proyecto-SIPA.png)

# VRID-AlumniUC - Proyecto SIPA
----
## Uniendo, Estandarizando, Limpiando Datos y Construcción del Grafo de Conocimiento (Neo4j)

> Avances y análisis exploratorios disponibles en [`data-analisis.ipynb`](data-analisis.ipynb).

---

## 📁 Estructura del Proyecto (`src/` y `scripts/`)

- `scripts/clean_sipa.py`: Script principal ejecutable que corre el pipeline completo de limpieza en memoria basado en Pandas.
- `scripts/build_graph.py`: Extractor y generador de nodos, relaciones y formateador para Neo4j (`Cypher` y `bulk import`).
- `scripts/load_to_neo4j.py`: Ingestador masivo en Neo4j mediante la librería oficial de Python (`neo4j` driver).
- `scripts/generate_graph_charts.py`: Generador de visualizaciones analíticas y grafo interactivo 3D HTML.
- `src/simple_clean.py`: Orquestador de limpieza base, desduplicación de celdas multivalor y recuperación de títulos por fallback.
- `src/author_linkage/`: Módulo de recuperación Nivel 1 de autores faltantes mediante catálogo hash de personas UC.
- `src/normalize_categories/`: Módulo de normalización de códigos Dewey (DDC), ODS bilingües y materias.
- `src/language_normalization/`: Módulo de estandarización de idiomas a ISO 639-1 (`en`, `es`).
- `src/rights_normalization/`: Módulo de unificación de derechos y permisos de acceso (`acceso abierto`, `acceso restringido`).
- `src/graph_builder/`: Módulo extractor de elementos de grafo (10 tipos de nodos y 11 tipos de relaciones).
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

## 📊 Grafo de Conocimiento en Neo4j

* **Total Nodos**: **576,299** (`:Work`, `:Person`, `:Department`, `:Dewey`, `:ODS`, `:Publisher`, `:Funder`, `:Doctype`, `:Source`, `:Keyword`)
* **Total Relaciones**: **2,490,546** (`AUTHORED`, `CO_AUTHORED_WITH`, `AFFILIATED_TO`, `CLASSIFIED_IN`, `CONTRIBUTES_TO_ODS`, `PUBLISHED_IN`, `COLLABORATES_WITH`, `FUNDED_BY`, `HAS_TYPE`, `INDEXED_IN`, `HAS_KEYWORD`)
* **Documentación Completa**: Consulte [`docs/DOCUMENTACION_GRAFO_NEO4J.md`](docs/DOCUMENTACION_GRAFO_NEO4J.md).

---

## 🚀 Ejecución del Pipeline Completo

Desde la raíz del proyecto:

1. **Limpieza y Normalización**:
   ```bash
   python scripts/clean_sipa.py
   ```
2. **Construcción de Archivos del Grafo**:
   ```bash
   python scripts/build_graph.py
   ```
3. **Carga en Neo4j Local**:
   ```bash
   python scripts/load_to_neo4j.py
   ```
4. **Generación de Gráficos Analíticos**:
   ```bash
   python scripts/generate_graph_charts.py
   ```

---

## 📄 Logs de Auditoría e Informes (`data/` y `docs/`)

- `data/EXPORT_SIPA_null_columns.log`: Registro de columnas eliminadas por estar 100% vacías.
- `data/EXPORT_SIPA_missing_titles.log`: Registro de los 1.379 registros sin título tras aplicar fallbacks.
- `docs/REPORTE_CALIDAD_Y_NORMALIZACION_SIPA.md`: Informe formal detallado de métricas y hallazgos.
- `docs/REPORTE_CALIDAD_Y_NORMALIZACION_SIPA.md`: Informe formal detallado de métricas y hallazgos.
- `docs/DOCUMENTACION_GRAFO_NEO4J.md`: Esquema del grafo, taxonomía de relaciones y consultas Cypher.
