#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Clustering con K-Medoids
Agrupa NNA según componentes principales
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans  # Fallback si K-Medoids falla
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from pathlib import Path

print("🎯 ANÁLISIS DE CLUSTERING")
print("=" * 60)

# Cargar scores factoriales
print("\n📂 Cargando scores factoriales...")
scores = pd.read_parquet("data/processed/factor_scores.parquet")
print(f"✅ {len(scores):,} registros cargados")

# Preparar datos (eliminar NaN)
scores_clean = scores.dropna()
print(f"✅ {len(scores_clean):,} registros sin valores faltantes")

# Extraer componentes principales
pc_cols = [col for col in scores_clean.columns if col.startswith('PC')]
X = scores_clean[pc_cols].values

print(f"\n📊 Dimensiones del espacio factorial:")
print(f"   • Observaciones: {X.shape[0]:,}")
print(f"   • Componentes: {X.shape[1]}")

# Validación de tamaños de cluster
def valid_sizes(labels, min_prop=0.05):
    """Verifica que cada cluster tenga al menos min_prop% de observaciones"""
    n = len(labels)
    vals, cnts = np.unique(labels, return_counts=True)
    min_size = cnts.min()
    min_pct = min_size / n
    return np.all(cnts / n >= min_prop), min_pct

# Determinar método de clustering
print("\n🔧 Seleccionando algoritmo de clustering...")
try:
    from sklearn_extra.cluster import KMedoids
    use_kmedoids = True
    print("✅ Usando K-Medoids (robusto a outliers)")
except ImportError:
    use_kmedoids = False
    print("⚠️  K-Medoids no disponible, usando K-Means")

# Evaluar diferentes valores de k
print("\n🔍 EVALUANDO DIFERENTES NÚMEROS DE CLUSTERS...")
candidates = range(3, 9)
results = []

for k in candidates:
    print(f"   Probando k={k}...", end=" ")
    
    if use_kmedoids:
        try:
            model = KMedoids(n_clusters=k, random_state=42, method="alternate")
            model.fit(X)
            labels = model.labels_
        except:
            # Fallback a KMeans si falla
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            model.fit(X)
            labels = model.labels_
    else:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        model.fit(X)
        labels = model.labels_
    
    # Calcular métricas
    sil = silhouette_score(X, labels)
    ch = calinski_harabasz_score(X, labels)
    valid, min_pct = valid_sizes(labels, min_prop=0.05)
    
    results.append({
        'k': k,
        'silhouette': sil,
        'calinski_harabasz': ch,
        'labels': labels,
        'valid_sizes': valid,
        'min_cluster_pct': min_pct
    })
    
    status = "✓" if valid else "✗"
    print(f"Silhouette={sil:.3f}, Min%={min_pct*100:.1f}% {status}")

# Convertir a DataFrame para análisis
results_df = pd.DataFrame(results)

# Seleccionar mejor k
print("\n🎯 SELECCIONANDO MEJOR CONFIGURACIÓN...")

# Prioridad 1: Tamaños válidos
valid_results = results_df[results_df['valid_sizes']].copy()

if len(valid_results) > 0:
    # Ordenar por silhouette
    valid_results = valid_results.sort_values('silhouette', ascending=False)
    best = valid_results.iloc[0]
    print(f"✅ Configuración óptima (tamaños válidos):")
else:
    # Si ninguno cumple, usar el mejor silhouette
    best = results_df.sort_values('silhouette', ascending=False).iloc[0]
    print(f"⚠️  Ninguna config. cumple tamaños mínimos, usando mejor silhouette:")

k_best = int(best['k'])
sil_best = best['silhouette']
labels_best = best['labels']

print(f"   • Clusters (k): {k_best}")
print(f"   • Silhouette: {sil_best:.3f}")
print(f"   • Calinski-Harabasz: {best['calinski_harabasz']:.1f}")
print(f"   • Tamaño mín. cluster: {best['min_cluster_pct']*100:.1f}%")

# Asignar clusters
print("\n💾 GUARDANDO RESULTADOS...")

Path("data/processed").mkdir(parents=True, exist_ok=True)
Path("reports/figures").mkdir(parents=True, exist_ok=True)

out = pd.DataFrame({
    'cluster': labels_best
}, index=scores_clean.index)

out.to_parquet("data/processed/cluster_assign.parquet", index=False)
print("✅ data/processed/cluster_assign.parquet")

# Distribución de clusters
print("\n📊 DISTRIBUCIÓN DE CLUSTERS:")
cluster_sizes = pd.Series(labels_best).value_counts().sort_index()

for cluster_id, size in cluster_sizes.items():
    pct = size / len(labels_best) * 100
    print(f"   Cluster {cluster_id}: {size:>6,} ({pct:>5.1f}%)")

cluster_sizes.to_csv("reports/cluster_sizes.csv", header=["n"])
print("\n✅ reports/cluster_sizes.csv")

# Visualizaciones
print("\n�� GENERANDO VISUALIZACIONES...")

# 1. Curva de Silhouette
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ks = results_df['k'].values
sils = results_df['silhouette'].values

ax1.plot(ks, sils, marker='o', linewidth=2, markersize=8, color='steelblue')
ax1.axvline(k_best, color='red', linestyle='--', alpha=0.7, label=f'k óptimo = {k_best}')
ax1.scatter([k_best], [sil_best], color='red', s=200, zorder=5, edgecolor='black', linewidth=2)
ax1.set_xlabel("Número de Clusters (k)", fontsize=11)
ax1.set_ylabel("Silhouette Score", fontsize=11)
ax1.set_title("Selección de k por Silhouette", fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend()

# 2. Distribución de tamaños
ax2.bar(cluster_sizes.index, cluster_sizes.values, color='steelblue', edgecolor='black')
ax2.axhline(len(labels_best) * 0.05, color='red', linestyle='--', 
            alpha=0.7, label='Umbral 5%')
ax2.set_xlabel("Cluster", fontsize=11)
ax2.set_ylabel("Número de Observaciones", fontsize=11)
ax2.set_title(f"Distribución de Clusters (k={k_best})", fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
ax2.legend()

plt.tight_layout()
plt.savefig("reports/figures/clustering_analysis.png", dpi=300, bbox_inches='tight')
plt.close()
print("✅ reports/figures/clustering_analysis.png")

# 3. Proyección 2D (PC1 vs PC2)
if X.shape[1] >= 2:
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter por cluster
    for cluster_id in range(k_best):
        mask = labels_best == cluster_id
        size = mask.sum()
        ax.scatter(X[mask, 0], X[mask, 1], 
                  label=f'Cluster {cluster_id} (n={size:,})',
                  alpha=0.6, s=30)
    
    ax.set_xlabel("PC1", fontsize=11)
    ax.set_ylabel("PC2", fontsize=11)
    ax.set_title(f"Clusters en Espacio Factorial (k={k_best})", 
                fontsize=13, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("reports/figures/clusters_2d.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ reports/figures/clusters_2d.png")

# Guardar métricas
metrics_df = results_df[['k', 'silhouette', 'calinski_harabasz', 'valid_sizes', 'min_cluster_pct']].copy()
metrics_df.to_csv("reports/clustering_metrics.csv", index=False)
print("✅ reports/clustering_metrics.csv")

# Reporte final
print("\n📋 RESUMEN FINAL")
print("=" * 60)
print(f"Método: {'K-Medoids' if use_kmedoids else 'K-Means'}")
print(f"Clusters óptimos (k): {k_best}")
print(f"Silhouette score: {sil_best:.3f}")
print(f"Observaciones clusterizadas: {len(labels_best):,}")
print(f"Cluster más pequeño: {cluster_sizes.min():,} ({cluster_sizes.min()/len(labels_best)*100:.1f}%)")
print(f"Cluster más grande: {cluster_sizes.max():,} ({cluster_sizes.max()/len(labels_best)*100:.1f}%)")

# Guardar reporte
with open("reports/clustering_report.txt", "w", encoding="utf-8") as f:
    f.write("REPORTE DE CLUSTERING\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Método: {'K-Medoids' if use_kmedoids else 'K-Means'}\n")
    f.write(f"Número óptimo de clusters: {k_best}\n")
    f.write(f"Silhouette score: {sil_best:.3f}\n")
    f.write(f"Observaciones: {len(labels_best):,}\n\n")
    f.write("Distribución de clusters:\n")
    for cluster_id, size in cluster_sizes.items():
        pct = size / len(labels_best) * 100
        f.write(f"  Cluster {cluster_id}: {size:>6,} ({pct:>5.1f}%)\n")

print("\n✅ reports/clustering_report.txt")
print("\n🎉 ¡Clustering completado!")
