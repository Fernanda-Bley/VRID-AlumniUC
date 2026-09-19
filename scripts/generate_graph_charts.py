"""
Script de Generación de Gráficos y Visualizaciones del Grafo de Conocimiento (VRID-AlumniUC)
-------------------------------------------------------------------------------------
Lee las tablas generadas en data/graph/ y produce:
1. Gráficos estáticos PNG en data/graph/charts/
2. Red interactiva HTML en data/graph/charts/interactive_interdepartmental_network.html

Ubicación: scripts/generate_graph_charts.py
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pyvis.network import Network

# Configuración de estilo de gráficos
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_GRAFO = os.path.join(BASE_DIR, "data", "graph")
DIR_CHARTS = os.path.join(DIR_GRAFO, "charts")
os.makedirs(DIR_CHARTS, exist_ok=True)

print("=== GENERANDO GRÁFICOS Y VISUALIZACIONES DEL GRAFO DE CONOCIMIENTO ===")

# Cargar tablas del grafo
df_nodes_dept = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_department.csv"))
df_nodes_ods = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_ods.csv"))
df_nodes_doctype = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_doctype.csv"))
df_nodes_source = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_source.csv"))
df_edges_aff = pd.read_csv(os.path.join(DIR_GRAFO, "edges_affiliated.csv"))
df_edges_ods = pd.read_csv(os.path.join(DIR_GRAFO, "edges_ods.csv"))
df_edges_interdept = pd.read_csv(os.path.join(DIR_GRAFO, "edges_interdepartmental.csv"))
df_edges_coauth = pd.read_csv(os.path.join(DIR_GRAFO, "edges_coauthored.csv"))
df_nodes_person = pd.read_csv(os.path.join(DIR_GRAFO, "nodes_person.csv"))

# ---------------------------------------------------------
# 1. Top 15 Unidades Académicas UC por Afiliaciones
# ---------------------------------------------------------
print("\n[1/5] Generando gráfico: Top Unidades Académicas UC...")
aff_counts = df_edges_aff["dept_id"].value_counts().reset_index()
aff_counts.columns = ["dept_id", "count"]
top_depts = pd.merge(aff_counts, df_nodes_dept, on="dept_id").head(15)

plt.figure(figsize=(10, 6))
ax = sns.barplot(data=top_depts, y="name", x="count", palette="Blues_r")
plt.title("Top 15 Unidades Académicas / Facultades UC por Afiliación de Autores", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Número de Afiliaciones Registradas", fontsize=11)
plt.ylabel("")

for p in ax.patches:
    width = p.get_width()
    ax.annotate(f"{int(width):,}", (width + 100, p.get_y() + p.get_height() / 2),
                ha='left', va='center', fontsize=9, color='#333333')

plt.tight_layout()
chart1_path = os.path.join(DIR_CHARTS, "chart_1_top_departments.png")
plt.savefig(chart1_path, dpi=300)
plt.close()
print(f"  -> Guardado: {chart1_path}")


# ---------------------------------------------------------
# 2. Distribución de Publicaciones por Objetivo ODS
# ---------------------------------------------------------
print("\n[2/5] Generando gráfico: Distribución de Publicaciones por ODS...")
ods_counts = df_edges_ods["ods_code"].value_counts().reset_index()
ods_counts.columns = ["ods_code", "count"]
ods_data = pd.merge(ods_counts, df_nodes_ods, on="ods_code").sort_values("count", ascending=False).head(15)

plt.figure(figsize=(10, 6))
ax = sns.barplot(data=ods_data, y="name_es", x="count", palette="YlOrRd_r")
plt.title("Publicaciones Científicas por Objetivo de Desarrollo Sostenible (ODS)", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Número de Publicaciones Asociadas", fontsize=11)
plt.ylabel("")

for p in ax.patches:
    width = p.get_width()
    ax.annotate(f"{int(width):,}", (width + 500, p.get_y() + p.get_height() / 2),
                ha='left', va='center', fontsize=9, color='#333333')

plt.tight_layout()
chart2_path = os.path.join(DIR_CHARTS, "chart_2_ods_distribution.png")
plt.savefig(chart2_path, dpi=300)
plt.close()
print(f"  -> Guardado: {chart2_path}")


# ---------------------------------------------------------
# 3. Top 15 Pares de Colaboración Interdepartamental UC
# ---------------------------------------------------------
print("\n[3/5] Generando gráfico: Red de Colaboración Interdepartamental...")
dept_map = dict(zip(df_nodes_dept["dept_id"], df_nodes_dept["name"]))
df_inter = df_edges_interdept.copy()
df_inter["dept1_name"] = df_inter["dept1_id"].map(dept_map)
df_inter["dept2_name"] = df_inter["dept2_id"].map(dept_map)
df_inter["pair"] = df_inter["dept1_name"] + " <-> " + df_inter["dept2_name"]
top_inter = df_inter.sort_values("weight", ascending=False).head(12)

plt.figure(figsize=(11, 6))
ax = sns.barplot(data=top_inter, y="pair", x="weight", hue="pair", palette="Purples_r", legend=False)
plt.title("Top Colaboraciones Interdisciplinarias entre Unidades UC", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Número de Obras Científicas Conjuntas", fontsize=11)
plt.ylabel("")

for p in ax.patches:
    width = p.get_width()
    ax.annotate(f"{int(width):,}", (width + 2, p.get_y() + p.get_height() / 2),
                ha='left', va='center', fontsize=9, color='#333333')

plt.tight_layout()
chart3_path = os.path.join(DIR_CHARTS, "chart_3_interdepartmental_collaboration.png")
plt.savefig(chart3_path, dpi=300)
plt.close()
print(f"  -> Guardado: {chart3_path}")


# ---------------------------------------------------------
# 4. Top Investigadores por Co-autorías Acumuladas
# ---------------------------------------------------------
print("\n[4/5] Generando gráfico: Top Investigadores por Co-autoría...")
p1_counts = df_edges_coauth.groupby("person1_id")["weight"].sum().reset_index()
p2_counts = df_edges_coauth.groupby("person2_id")["weight"].sum().reset_index()
p1_counts.columns = ["person_id", "weight"]
p2_counts.columns = ["person_id", "weight"]
total_coauth = pd.concat([p1_counts, p2_counts]).groupby("person_id")["weight"].sum().reset_index()
top_investigators = pd.merge(total_coauth, df_nodes_person, on="person_id").sort_values("weight", ascending=False).head(15)

plt.figure(figsize=(10, 6))
ax = sns.barplot(data=top_investigators, y="name", x="weight", hue="name", palette="Greens_r", legend=False)
plt.title("Top 15 Investigadores UC con Mayor Volumen de Co-autorías", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Total de Enlaces de Co-autoría (Peso Acumulado)", fontsize=11)
plt.ylabel("")

for p in ax.patches:
    width = p.get_width()
    ax.annotate(f"{int(width):,}", (width + 10, p.get_y() + p.get_height() / 2),
                ha='left', va='center', fontsize=9, color='#333333')

plt.tight_layout()
chart4_path = os.path.join(DIR_CHARTS, "chart_4_top_coauthorship.png")
plt.savefig(chart4_path, dpi=300)
plt.close()
print(f"  -> Guardado: {chart4_path}")


# ---------------------------------------------------------
# 5. Visualización Interactiva HTML (PyVis) - Red Interdepartamental
# ---------------------------------------------------------
print("\n[5/5] Generando red interactiva HTML: PyVis Interdepartmental Network...")
net = Network(height="750px", width="100%", bgcolor="#1a1a2e", font_color="white", heading="Red Interdisciplinaria de Unidades UC")

active_inter = df_inter[df_inter["weight"] >= 5]
nodes_in_net = set(active_inter["dept1_id"]).union(set(active_inter["dept2_id"]))

for d_id in nodes_in_net:
    d_name = dept_map.get(d_id, d_id)
    net.add_node(d_id, label=d_name, title=d_name, color="#00adb5", size=20)

for _, row in active_inter.iterrows():
    w = int(row["weight"])
    net.add_edge(row["dept1_id"], row["dept2_id"], value=w, title=f"Obras conjuntas: {w}", color="#00fff5")

net.barnes_hut()
html_net_path = os.path.join(DIR_CHARTS, "interactive_interdepartmental_network.html")
net.save_graph(html_net_path)
print(f"  -> Guardado: {html_net_path}")


print("\n=== TODOS LOS GRÁFICOS Y LA RED INTERACTIVA FUERON GENERADOS CON ÉXITO ===")
print(f"Carpeta de gráficos: {DIR_CHARTS}")
