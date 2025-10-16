#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ingeniería de variable objetivo: trabaja (Sí/No)
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

print("🎯 INGENIERÍA DE VARIABLE OBJETIVO")
print("=" * 60)

# Cargar datos
print("\n📂 Cargando datos...")
df = pd.read_parquet("data/processed/base_clean.parquet")
print(f"✅ {len(df):,} registros cargados")

# Crear o cargar hints
hints_path = Path("reports/columns_hints.json")
if not hints_path.exists():
    print("\n⚠️  Archivo columns_hints.json no existe, creando configuración por defecto...")
    
    # Buscar columnas relacionadas con trabajo
    cols_lower = {col: col.lower() for col in df.columns}
    
    hints = {
        "trabaja_explicit_cols": [
            col for col, lower in cols_lower.items() 
            if "trabajo" in lower and "protegido" not in lower and "desvinculado" not in lower
        ],
        "trabajo_protegido_cols": [
            col for col, lower in cols_lower.items() 
            if "trabajo_protegido" in lower or "protegido" in lower
        ],
        "desvinculado_cols": [
            col for col, lower in cols_lower.items() 
            if "desvinculado" in lower
        ]
    }
    
    # Guardar hints
    Path("reports").mkdir(parents=True, exist_ok=True)
    with open(hints_path, "w", encoding="utf-8") as f:
        json.dump(hints, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Creado: {hints_path}")
else:
    with open(hints_path, "r", encoding="utf-8") as f:
        hints = json.load(f)
    print(f"✅ Cargado: {hints_path}")

# Mostrar columnas detectadas
print("\n🔍 COLUMNAS DETECTADAS:")
print(f"  • Trabajo explícito: {hints.get('trabaja_explicit_cols', [])}")
print(f"  • Trabajo protegido: {hints.get('trabajo_protegido_cols', [])}")
print(f"  • Desvinculado: {hints.get('desvinculado_cols', [])}")

def map_bin(col_name):
    """Mapea columna a binario (1=Sí, 0=No)"""
    if col_name is None or col_name not in df.columns:
        return pd.Series([np.nan] * len(df), index=df.index)
    
    # Normalizar valores
    v = (df[col_name].astype(str)
         .str.strip()
         .str.lower()
         .replace({"sí": "si", "nan": np.nan}))
    
    # Mapear a binario
    m = v.map({
        "si": 1, "yes": 1, "1": 1, "1.0": 1, "true": 1,
        "no": 0, "0": 0, "0.0": 0, "false": 0
    })
    
    return pd.to_numeric(m, errors="coerce")

# Inicializar variable objetivo
print("\n⚙️  CONSTRUYENDO VARIABLE OBJETIVO...")
y = pd.Series(np.nan, index=df.index, dtype="float")

# Contador de casos
stats = {
    "explicito": 0,
    "trabajo_protegido": 0,
    "desvinculado": 0,
    "sin_info": 0
}

# 3) Trabajo explícito (máxima prioridad)
explicits = [c for c in hints.get("trabaja_explicit_cols", []) if c in df.columns]
if explicits:
    col = explicits[0]
    print(f"  1️⃣  Usando '{col}' para trabajo explícito...")
    y_temp = map_bin(col)
    mask_explicit = ~y_temp.isna()
    y[mask_explicit] = y_temp[mask_explicit]
    stats["explicito"] = mask_explicit.sum()
    print(f"     → {stats['explicito']:,} casos asignados")

# 2) Trabajo protegido ⇒ 1 cuando y es NA
tp_cols = [c for c in hints.get("trabajo_protegido_cols", []) if c in df.columns]
if tp_cols:
    col = tp_cols[0]
    print(f"  2️⃣  Usando '{col}' para trabajo protegido...")
    tp = map_bin(col)
    mask_tp = y.isna() & (tp == 1)
    y[mask_tp] = 1.0
    stats["trabajo_protegido"] = mask_tp.sum()
    print(f"     → {stats['trabajo_protegido']:,} casos adicionales asignados")

# 1) Desvinculado ⇒ 0; no desvinculado ⇒ 1 cuando y es NA
dz_cols = [c for c in hints.get("desvinculado_cols", []) if c in df.columns]
if dz_cols:
    col = dz_cols[0]
    print(f"  3️⃣  Usando '{col}' para desvinculados...")
    d = map_bin(col)  # 1=desvinculado, 0=no desvinculado
    
    # Invertir: si fue desvinculado → antes trabajaba (1), ahora no (0)
    # Si NO fue desvinculado → sigue trabajando (1)
    mask_desv = y.isna() & (d == 1)
    mask_no_desv = y.isna() & (d == 0)
    
    y[mask_desv] = 0.0  # Desvinculado = ya no trabaja
    y[mask_no_desv] = 1.0  # No desvinculado = sigue trabajando
    
    stats["desvinculado"] = (mask_desv | mask_no_desv).sum()
    print(f"     → {stats['desvinculado']:,} casos adicionales asignados")

# Casos sin información
stats["sin_info"] = y.isna().sum()

# Crear dataframe de salida
print("\n💾 GUARDANDO RESULTADOS...")
out = pd.DataFrame({
    "trabaja": y
}, index=df.index)

# Guardar
Path("data/processed").mkdir(parents=True, exist_ok=True)
out.to_parquet("data/processed/target_trabaja.parquet", index=False)
out.to_csv("reports/target_decisions.csv", index=False)

print("✅ data/processed/target_trabaja.parquet")
print("✅ reports/target_decisions.csv")

# Reporte final
print("\n📊 RESUMEN DE VARIABLE OBJETIVO")
print("=" * 60)
print(f"Total registros:           {len(df):>10,}")
print(f"  • Trabajo explícito:     {stats['explicito']:>10,} ({stats['explicito']/len(df)*100:>5.1f}%)")
print(f"  • Trabajo protegido:     {stats['trabajo_protegido']:>10,} ({stats['trabajo_protegido']/len(df)*100:>5.1f}%)")
print(f"  • Inferido desvinculado: {stats['desvinculado']:>10,} ({stats['desvinculado']/len(df)*100:>5.1f}%)")
print(f"  • Sin información:       {stats['sin_info']:>10,} ({stats['sin_info']/len(df)*100:>5.1f}%)")
print()
print(f"Trabaja = 1 (Sí):          {(y==1).sum():>10,} ({(y==1).sum()/len(df)*100:>5.1f}%)")
print(f"Trabaja = 0 (No):          {(y==0).sum():>10,} ({(y==0).sum()/len(df)*100:>5.1f}%)")
print(f"Sin clasificar:            {y.isna().sum():>10,} ({y.isna().sum()/len(df)*100:>5.1f}%)")

# Guardar reporte
with open("reports/target_engineering_report.txt", "w", encoding="utf-8") as f:
    f.write("REPORTE DE INGENIERÍA DE VARIABLE OBJETIVO\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Total registros: {len(df):,}\n\n")
    f.write("Distribución de la variable 'trabaja':\n")
    f.write(f"  • Sí trabaja (1): {(y==1).sum():,} ({(y==1).sum()/len(df)*100:.1f}%)\n")
    f.write(f"  • No trabaja (0): {(y==0).sum():,} ({(y==0).sum()/len(df)*100:.1f}%)\n")
    f.write(f"  • Sin datos:      {y.isna().sum():,} ({y.isna().sum()/len(df)*100:.1f}%)\n\n")
    f.write("Origen de la información:\n")
    f.write(f"  1. Trabajo explícito:     {stats['explicito']:,}\n")
    f.write(f"  2. Trabajo protegido:     {stats['trabajo_protegido']:,}\n")
    f.write(f"  3. Inferido desvinculado: {stats['desvinculado']:,}\n")

print("✅ reports/target_engineering_report.txt")
print("\n🎉 ¡Proceso completado!")

if __name__ == "__main__":
    pass
