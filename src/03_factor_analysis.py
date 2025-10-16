#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis factorial mediante PCA
Incluye codificación de variables categóricas
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from pathlib import Path

print("🔬 ANÁLISIS FACTORIAL (PCA)")
print("=" * 60)

# Cargar datos
print("\n📂 Cargando datos...")
df = pd.read_parquet("data/processed/base_clean.parquet")
print(f"✅ {len(df):,} registros cargados")

# Columnas a excluir
drop_keys = [
    "trabaja", "desvinculado", "trabajo_protegido",  # Variables objetivo/fuga
    "nombre", "apellido",  # Identificadores personales
    "id", "fic", "ficha",  # IDs
]

print("\n🔍 SELECCIONANDO Y CODIFICANDO VARIABLES...")

# Filtrar columnas
keep_cols = []
for col in df.columns:
    col_lower = col.lower()
    if not any(k in col_lower for k in drop_keys):
        keep_cols.append(col)

print(f"Variables candidatas: {len(keep_cols)}")

# Separar numéricas y categóricas
X_num = df[keep_cols].select_dtypes(include=[np.number]).copy()
X_cat = df[keep_cols].select_dtypes(include=['object']).copy()

print(f"\n📊 Variables encontradas:")
print(f"   • Numéricas: {X_num.shape[1]}")
print(f"   • Categóricas: {X_cat.shape[1]}")

# Imputar numéricas
if X_num.shape[1] > 0:
    X_num = X_num.fillna(X_num.median())
    print(f"✅ Variables numéricas imputadas")
    print(f"   Columnas: {', '.join(X_num.columns[:5])}{'...' if len(X_num.columns) > 5 else ''}")

# Codificar categóricas (Label Encoding para las más importantes)
X_encoded_list = []

if X_cat.shape[1] > 0:
    print(f"\n🔧 CODIFICANDO VARIABLES CATEGÓRICAS...")
    
    for col in X_cat.columns:
        # Solo procesar columnas con menos de 50 categorías únicas
        n_unique = df[col].nunique()
        
        if n_unique < 2:
            continue  # Skip constantes
        
        if n_unique <= 50:
            # Label encoding
            temp = df[col].fillna('Desconocido').astype(str)
            le = LabelEncoder()
            encoded = le.fit_transform(temp)
            X_encoded_list.append(pd.Series(encoded, name=f"{col}_encoded", index=df.index))
            print(f"   ✓ {col}: {n_unique} categorías → encoded")
        else:
            print(f"   ⊘ {col}: {n_unique} categorías (omitida, demasiadas)")

# Combinar todas las variables
X_parts = []

if X_num.shape[1] > 0:
    X_parts.append(X_num)

if X_encoded_list:
    X_encoded = pd.concat(X_encoded_list, axis=1)
    X_parts.append(X_encoded)

if not X_parts:
    print("\n❌ ERROR: No hay variables suficientes para el análisis")
    exit(1)

X = pd.concat(X_parts, axis=1)

# Eliminar columnas con varianza cero
X = X.loc[:, X.std() > 0]

print(f"\n✅ Dataset final para PCA:")
print(f"   • Total variables: {X.shape[1]}")
print(f"   • Registros: {X.shape[0]:,}")

if X.shape[1] < 2:
    print("\n⚠️  ERROR: Se necesitan al menos 2 variables para PCA")
    exit(1)

# Estandarización
print("\n📐 Estandarizando variables...")
sc = StandardScaler()
Z = sc.fit_transform(X)
print("✅ Estandarización completada")

# PCA
n_comp = min(10, Z.shape[1])
print(f"\n🎯 EJECUTANDO PCA ({n_comp} componentes)...")

pca = PCA(n_components=n_comp, random_state=42)
F = pca.fit_transform(Z)

print("✅ PCA completado")
print(f"   Varianza explicada total: {pca.explained_variance_ratio_.sum()*100:.1f}%")

# Guardar resultados
print("\n💾 GUARDANDO RESULTADOS...")

Path("data/processed").mkdir(parents=True, exist_ok=True)
Path("reports/figures").mkdir(parents=True, exist_ok=True)

# Scores
scores = pd.DataFrame(
    F, 
    columns=[f"PC{i+1}" for i in range(F.shape[1])]
)
scores.to_parquet("data/processed/factor_scores.parquet", index=False)
print("✅ data/processed/factor_scores.parquet")

# Cargas factoriales
loadings = pd.DataFrame(
    pca.components_.T,
    index=X.columns,
    columns=[f"PC{i+1}" for i in range(F.shape[1])]
)
loadings.to_csv("reports/factor_loadings.csv")
print("✅ reports/factor_loadings.csv")

# Top cargas por componente
print("\n📋 TOP CARGAS FACTORIALES:")
for i in range(min(3, n_comp)):
    pc = f"PC{i+1}"
    top_pos = loadings[pc].nlargest(3)
    top_neg = loadings[pc].nsmallest(3)
    print(f"\n  {pc} ({pca.explained_variance_ratio_[i]*100:.1f}% varianza):")
    print("    Positivas:")
    for var, val in top_pos.items():
        print(f"      • {var}: {val:.3f}")
    print("    Negativas:")
    for var, val in top_neg.items():
        print(f"      • {var}: {val:.3f}")

# Varianza explicada
evr = pd.DataFrame({
    "component": [f"PC{i+1}" for i in range(F.shape[1])],
    "explained_variance_ratio": pca.explained_variance_ratio_,
    "cumulative_variance": np.cumsum(pca.explained_variance_ratio_)
})
evr.to_csv("reports/pca_explained_variance.csv", index=False)
print("\n✅ reports/pca_explained_variance.csv")

# Visualizaciones
print("\n📊 GENERANDO VISUALIZACIONES...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Scree plot
ax1.plot(range(1, len(pca.explained_variance_ratio_) + 1),
         pca.explained_variance_ratio_, 
         marker='o', linewidth=2, markersize=8, color='steelblue')
ax1.set_xlabel("Componente Principal", fontsize=11)
ax1.set_ylabel("Varianza Explicada", fontsize=11)
ax1.set_title("Scree Plot", fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0.1, color='r', linestyle='--', alpha=0.5)

# Varianza acumulada
ax2.plot(range(1, len(pca.explained_variance_ratio_) + 1),
         np.cumsum(pca.explained_variance_ratio_),
         marker='s', linewidth=2, markersize=8, color='green')
ax2.set_xlabel("Número de Componentes", fontsize=11)
ax2.set_ylabel("Varianza Acumulada", fontsize=11)
ax2.set_title("Varianza Acumulada", fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0.8, color='r', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig("reports/figures/scree_pca.png", dpi=300, bbox_inches='tight')
plt.close()
print("✅ reports/figures/scree_pca.png")

# Reporte final
print("\n📊 RESUMEN FINAL")
print("=" * 60)
print(f"Variables totales:         {X.shape[1]}")
print(f"  • Numéricas originales:  {X_num.shape[1]}")
print(f"  • Categóricas codif.:    {len(X_encoded_list) if X_encoded_list else 0}")
print(f"Componentes extraídos:     {F.shape[1]}")
print(f"Varianza PC1:              {pca.explained_variance_ratio_[0]*100:.1f}%")
print(f"Varianza total:            {pca.explained_variance_ratio_.sum()*100:.1f}%")

# Guardar reporte
with open("reports/pca_report.txt", "w", encoding="utf-8") as f:
    f.write("REPORTE DE ANÁLISIS FACTORIAL (PCA)\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Variables analizadas: {X.shape[1]}\n")
    f.write(f"  • Numéricas: {X_num.shape[1]}\n")
    f.write(f"  • Categóricas codificadas: {len(X_encoded_list) if X_encoded_list else 0}\n")
    f.write(f"Observaciones: {X.shape[0]:,}\n")
    f.write(f"Componentes: {F.shape[1]}\n\n")
    f.write("Varianza explicada:\n")
    for i, (comp, var, cum) in evr.iterrows():
        f.write(f"  {comp}: {var*100:5.2f}% (acum: {cum*100:5.2f}%)\n")
    f.write("\nTop 5 cargas PC1:\n")
    for var, val in loadings['PC1'].abs().nlargest(5).items():
        f.write(f"  • {var}: {loadings.loc[var, 'PC1']:.3f}\n")

print("✅ reports/pca_report.txt")
print("\n🎉 ¡Análisis factorial completado!")
