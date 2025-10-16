#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportion_confint
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import geopandas as gpd

# Paths y nombres
DATA_PATH = "/workspaces/NNA_7/data/raw/Data_Limpia.xlsx"
OUTPUT_DIR = "/workspaces/NNA_7/reports/analisis_prevalencias_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
EXCEL_OUT = os.path.join(OUTPUT_DIR, "prevalencias_resultados.xlsx")

# Nombres de columnas según confirmaste
period_col = "Base_Origen"
cluster_col = "cluster"
territorio_col = "Localidad_fic"
case_col = "NNA DESVINCULADO DE LA ACTIVIDAD LABORAL"  # binaria 1/0

# Leer datos
df = pd.read_excel(DATA_PATH)
print(f"Los datos se leyeron correctamente")
df["cluster"] = pd.read_parquet("/workspaces/NNA_7/data/processed/cluster_assign.parquet")
print(df["cluster"].unique())

# Limpieza básica: uniformizar nombres, quitar filas sin periodo/cluster/territorio o sin variable de caso
df = df.rename(columns=lambda x: x.strip() if isinstance(x, str) else x)
required_cols = [period_col, cluster_col, territorio_col, case_col]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise FileNotFoundError(f"Faltan columnas esperadas en el archivo: {missing}")

df = df[required_cols].copy()

# Asegurar tipo binario (0/1) - intentar mapear valores no numéricos si aparecen
def make_binary(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float)) and not np.isnan(x):
        if x in (0,1):
            return int(x)
        # si viene como porcentaje pequeño o categórico, intentar heurística
        return int(x)
    s = str(x).strip().lower()
    if s in ("1","si","sí","y","yes","true","t","case","caso","s"):
        return 1
    if s in ("0","no","n","false","f","no case","no caso","nc"):
        return 0
    # si no se puede decidir, retornar NaN
    return np.nan

df[case_col] = df[case_col].map(make_binary)

# Función para calcular prevalencia y CI de Wilson
def calc_prevalence_ci(k, n, alpha=0.05):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    # proportion_confint devuelve (low, high)
    ci_low, ci_upp = proportion_confint(count=k, nobs=n, alpha=alpha, method='wilson')
    p = k / n
    return (p, ci_low, ci_upp)

# 1) Prevalencia por periodo × cluster
group1 = df.groupby([period_col, cluster_col])[case_col].agg(['sum','count']).reset_index()
group1.columns = [period_col, cluster_col, 'cases', 'n']
group1[['prevalence','ci_low','ci_high']] = group1.apply(lambda row: pd.Series(calc_prevalence_ci(int(row['cases']), int(row['n']))), axis=1)

# Guardar y mostrar
print("Prevalencia_periodo_x_cluster", group1.sort_values([period_col, 'prevalence'], ascending=[True, False]).head(200))
group1.to_csv(os.path.join(OUTPUT_DIR, "prevalencia_periodo_cluster.csv"), index=False)

# 2) Prevalencia por periodo × territorio × cluster (solo n >= 30)
group2 = df.groupby([period_col, territorio_col, cluster_col])[case_col].agg(['sum','count']).reset_index()
group2.columns = [period_col, territorio_col, cluster_col, 'cases', 'n']
group2 = group2[group2['n'] >= 30].copy()
group2[['prevalence','ci_low','ci_high']] = group2.apply(lambda row: pd.Series(calc_prevalence_ci(int(row['cases']), int(row['n']))), axis=1)

print("Prevalencia_periodo_territorio_cluster_n30", group2.sort_values([period_col, 'prevalence'], ascending=[True, False]).head(200))
group2.to_csv(os.path.join(OUTPUT_DIR, "prevalencia_periodo_territorio_cluster_n30.csv"), index=False)

# 3) Tablas resumen y archivo Excel con hojas
with pd.ExcelWriter(EXCEL_OUT) as writer:
    group1.to_excel(writer, sheet_name="periodo_cluster", index=False)
    group2.to_excel(writer, sheet_name="periodo_territorio_cluster_n30", index=False)
    df.to_excel(writer, sheet_name="datos_limpios", index=False)

# 4) Visualizaciones: barras con IC por periodo × cluster
plt.figure(figsize=(11,6))
# Tomamos el periodo más reciente y los dos anteriores si existen para ejemplificar; pero haremos gráficas por periodo
periods = sorted(df[period_col].dropna().unique())
plots_saved = []
for per in periods:
    sub = group1[group1[period_col] == per].sort_values('prevalence', ascending=False)
    if sub.empty:
        continue
    fig, ax = plt.subplots(figsize=(10,5))
    yerr_lower = np.maximum(0, sub['prevalence'] - sub['ci_low'])
    yerr_upper = np.maximum(0, sub['ci_high'] - sub['prevalence'])
    ax.errorbar(
    x=sub[cluster_col].astype(str),
    y=sub['prevalence'],
    yerr=[yerr_lower, yerr_upper],
    fmt='o', capsize=5, linestyle='None'
    )
    ax.set_ylim(0, min(1, sub['prevalence'].max()*1.25 + 0.02))
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Prevalencia")
    ax.set_title(f"Prevalencia (Wilson 95%) por Cluster - Periodo {per}")
    plt.xticks(rotation=45)
    fn = os.path.join(OUTPUT_DIR, f"prevalencia_cluster_periodo_{per}.png")
    fig.tight_layout()
    fig.savefig(fn, dpi=150)
    plt.close(fig)
    plots_saved.append(fn)

# 5) Heatmap (periodo x territorio) usando prevalencia agregada (independiente de cluster) - útil para detectar zonas
pivot = df.groupby([period_col, territorio_col])[case_col].agg(['sum','count']).reset_index()
pivot['prevalence'] = pivot['sum'] / pivot['count']
heat = pivot.pivot(index=territorio_col, columns=period_col, values='prevalence').fillna(0)
# Guardar CSV
heat.to_csv(os.path.join(OUTPUT_DIR, "heatmap_prevalence_territorio_periodo.csv"))

# Dibujar heatmap (si hay suficientes territorios)
fig, ax = plt.subplots(figsize=(10, max(6, 0.25*len(heat.index))))
sns.heatmap(heat, annot=False, ax=ax)
ax.set_title("Heatmap de prevalencia por Territorio (filas) × Periodo (columnas)")
fig.tight_layout()
heatmap_file = os.path.join(OUTPUT_DIR, "heatmap_prevalencia_territorio_periodo.png")
fig.savefig(heatmap_file, dpi=150)
plt.close(fig)

# 6) Post-hoc territorial: Chi-cuadrado por periodo comparando distribución de casos entre territorios
# Para cada periodo, construimos una tabla de contingencia (territorio x case) y hacemos chi2.
chi_results = []
for per in periods:
    sub = df[df[period_col]==per]
    if sub.empty:
        continue
    cont = pd.crosstab(sub[territorio_col], sub[case_col])  # columnas 0/1
    print(cont)
    # Queremos ver si hay diferencia en proporciones entre territorios
    try:
        chi2, p, dof, ex = stats.chi2_contingency(cont.fillna(0))
    except Exception as e:
        chi2, p, dof = np.nan, np.nan, np.nan
    chi_results.append({'periodo': per, 'chi2': chi2, 'p_value': p, 'dof': dof, 'n_territorios': cont.shape[0]})

chi_df = pd.DataFrame(chi_results)
print("Chi2_por_periodo_territorio_vs_caso", chi_df)
chi_df.to_csv(os.path.join(OUTPUT_DIR, "chi2_por_periodo_territorio.csv"), index=False)

# 7) Identificar territorios 'hotspots' por periodo: calcular z-score de prevalencia y marcar top 10% o z>1.96
hotspots = []
for per in periods:
    sub = pivot[pivot[period_col]==per].copy()
    if sub.empty:
        continue
    subs = sub.copy()
    subs['prevalence'] = subs['sum'] / subs['count']
    mean_p = subs['prevalence'].mean()
    std_p = subs['prevalence'].std(ddof=0)
    subs['z_score'] = (subs['prevalence'] - mean_p) / (std_p if std_p>0 else 1e-9)
    subs['is_hotspot_z1.96'] = subs['z_score'].abs() > 1.96
    # top 10% by prevalence
    thresh = subs['prevalence'].quantile(0.9)
    subs['is_hotspot_top10pct'] = subs['prevalence'] >= thresh
    subs['periodo'] = per
    hotspots.append(subs.reset_index()[[territorio_col, 'periodo', 'prevalence', 'z_score', 'is_hotspot_z1.96', 'is_hotspot_top10pct', 'count'] if 'count' in subs.columns else [territorio_col, 'periodo', 'prevalence', 'z_score', 'is_hotspot_z1.96', 'is_hotspot_top10pct']])

# Concatenar hotspots
hotspots_df = pd.concat(hotspots, ignore_index=True)
# Si 'count' no existe, añadir n desde pivot table
if 'count' not in hotspots_df.columns:
    counts = pivot.groupby([territorio_col])[ 'count' ].sum() if 'count' in pivot.columns else None
hotspots_df.to_csv(os.path.join(OUTPUT_DIR, "hotspots_z_top10pct.csv"), index=False)
print("Hotspots_identificados", hotspots_df.sort_values(['periodo','prevalence'], ascending=[True, False]).head(200))

# 8) Mapas (si hay GeoJSON o shapefile en /mnt/data)
# Buscamos archivos geo en el directorio /mnt/data
geo_candidates = [f for f in os.listdir("/workspaces/NNA_7/data/raw") if f.lower().endswith(('.geojson','.shp','.gpkg'))]
print(geo_candidates)
map_files = []
geo_gdf = None
if geo_candidates:
    # Prefer geojson
    geo_path = os.path.join("/workspaces/NNA_7/data/raw/", geo_candidates[0])
    try:
        geo_gdf = gpd.read_file(geo_path)
        map_files.append(geo_path)
        print(geo_gdf)
    except Exception as e:
        geo_gdf = None
        print(f"No se leyó")

if geo_gdf is not None:
    # Intentar unir por nombre de localidad. Normalizamos nombres para facilitar match.
    geo_gdf['name_norm'] = geo_gdf.columns[0]  # dummy
    # Buscaremos columna que coincida parcialmente con territorio_col
    possible_name_cols = [c for c in geo_gdf.columns if geo_gdf[c].dtype == object]
    # Escoger la columna con mayor número de matches por texto
    best_col = None
    best_matches = -1
    for c in possible_name_cols:
        # normalizar
        geo_gdf['_tmp'] = geo_gdf[c].astype(str).str.lower().str.replace(r'[^a-z0-9áéíóúñ ]','', regex=True).str.strip()
        # prepare territory names normalized
        terr_norm = df[territorio_col].astype(str).str.lower().str.replace(r'[^a-z0-9áéíóúñ ]','', regex=True).str.strip().unique()
        matches = geo_gdf['_tmp'].isin(terr_norm).sum()
        if matches > best_matches:
            best_matches = matches; best_col = c
    if best_col is None or best_matches == 0:
        # no match encontrado: guardamos archivo para que el usuario lo revise
        geo_map_note = f"No se encontró una coincidencia adecuada entre {territorio_col} y columnas textuales del archivo geo ({geo_candidates[0]})."
        print(geo_map_note)
    else:
        geo_gdf['name_norm'] = geo_gdf[best_col].astype(str).str.lower().str.replace(r'[^a-z0-9áéíóúñ ]','', regex=True).str.strip()
        df['name_norm'] = df[territorio_col].astype(str).str.lower().str.replace(r'[^a-z0-9áéíóúñ ]','', regex=True).str.strip()
        # Prevalencia agregada por territorio y periodo
        pref = pivot.copy()
        pref['name_norm'] = pref[territorio_col].astype(str).str.lower().str.replace(r'[^a-z0-9áéíóúñ ]','', regex=True).str.strip()
        # Unir y crear mapa por periodo (guardar un mapa por periodo)
        for per in periods:
            per_pref = pref[pref[period_col]==per].copy()
            merged = geo_gdf.merge(per_pref, left_on='name_norm', right_on='name_norm', how='left')
            # Plot
            fig, ax = plt.subplots(1,1, figsize=(8,8))
            merged.plot(column='prevalence', ax=ax, legend=True, missing_kwds={"color": "lightgrey", "label": "No data"})
            ax.set_title(f"Mapa de prevalencia por {territorio_col} - Periodo {per}")
            ax.axis('off')
            mfile = os.path.join(OUTPUT_DIR, f"map_prevalencia_{per}.png")
            fig.tight_layout()
            fig.savefig(mfile, dpi=150)
            plt.close(fig)
            map_files.append(mfile)

# 9) Guardar resumen final y listar archivos generados
generated_files = os.listdir(OUTPUT_DIR)
gen_df = pd.DataFrame({"archivo": generated_files})
print("Archivos_generados_en_output", gen_df)

print("Análisis completo. Los archivos resultantes se encuentran en:", OUTPUT_DIR)
print("Archivo Excel con resultados principales:", EXCEL_OUT)