#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análisis exploratorio de datos NNA
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuración
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data():
    """Carga datos desde Excel"""
    print("📂 Cargando datos...")
    raw_path = Path("data/raw")
    
    files = list(raw_path.glob("*.xlsx")) + list(raw_path.glob("*.xls"))
    if not files:
        raise FileNotFoundError("No hay archivos Excel en data/raw/")
    
    dfs = []
    for file in files:
        print(f"  ↳ {file.name}")
        try:
            df = pd.read_excel(file)
            dfs.append(df)
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
    
    if not dfs:
        raise ValueError("No se pudo cargar ningún archivo")
    
    df = pd.concat(dfs, ignore_index=True)
    print(f"✅ Cargados {len(df):,} registros de {len(dfs)} archivo(s)")
    return df

def clean_columns(df):
    """Limpia nombres de columnas"""
    df.columns = (df.columns
                  .str.strip()
                  .str.lower()
                  .str.replace(r'\s+', '_', regex=True)
                  .str.replace(r'[áàâã]', 'a', regex=True)
                  .str.replace(r'[éèê]', 'e', regex=True)
                  .str.replace(r'[íìî]', 'i', regex=True)
                  .str.replace(r'[óòôõ]', 'o', regex=True)
                  .str.replace(r'[úùû]', 'u', regex=True)
                  .str.replace(r'ñ', 'n', regex=True)
                  .str.replace(r'[^\w]', '_', regex=True))
    return df

def fix_mixed_types(df):
    """Convierte columnas con tipos mixtos a string"""
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).replace('nan', np.nan)
    return df

def infer_territorio(df):
    """Infiere columnas de territorio"""
    out = df.copy()
    
    loc_candidates = [c for c in out.columns if 'localidad' in c.lower()]
    upz_candidates = [c for c in out.columns if 'upz' in c.lower()]
    
    if loc_candidates:
        loc_col = loc_candidates[0]
        out['localidad'] = out[loc_col].astype(str).str.strip()
        loc_std = out['localidad'].value_counts()
    else:
        out['localidad'] = 'No especificada'
        loc_std = pd.Series({'No especificada': len(out)})
    
    if upz_candidates:
        upz_col = upz_candidates[0]
        out['upz'] = out[upz_col].astype(str).str.strip()
        upz_std = out['upz'].value_counts()
    else:
        out['upz'] = 'No especificada'
        upz_std = pd.Series({'No especificada': len(out)})
    
    return out, loc_std, upz_std

def analyze_demographics(df):
    """Análisis demográfico básico"""
    print("\n👥 ANÁLISIS DEMOGRÁFICO")
    print("=" * 50)
    
    edad_cols = [c for c in df.columns if 'edad' in c.lower()]
    genero_cols = [c for c in df.columns if any(x in c.lower() for x in ['genero', 'sexo'])]
    
    results = {}
    
    if edad_cols:
        edad_col = edad_cols[0]
        print(f"\n📊 Edad (columna: {edad_col}):")
        print(df[edad_col].describe())
        results['edad'] = df[edad_col].value_counts().head(10)
    
    if genero_cols:
        genero_col = genero_cols[0]
        print(f"\n⚧ Género (columna: {genero_col}):")
        print(df[genero_col].value_counts())
        results['genero'] = df[genero_col].value_counts()
    
    return results

def main():
    """Ejecuta análisis completo"""
    df = load_data()
    df = clean_columns(df)
    
    print(f"\n📋 INFORMACIÓN BÁSICA")
    print("=" * 50)
    print(f"Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    print(f"\nColumnas disponibles:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print(f"\n🗺️  ANÁLISIS TERRITORIAL")
    print("=" * 50)
    df, loc_counts, upz_counts = infer_territorio(df)
    
    print("\n📍 Top 10 Localidades:")
    print(loc_counts.head(10))
    
    print("\n📍 Top 10 UPZ:")
    print(upz_counts.head(10))
    
    demo_results = analyze_demographics(df)
    
    print(f"\n❓ VALORES FALTANTES")
    print("=" * 50)
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'faltantes': missing,
        'porcentaje': missing_pct
    })
    missing_df = missing_df[missing_df['faltantes'] > 0].sort_values('faltantes', ascending=False)
    
    if len(missing_df) > 0:
        print(missing_df.head(15))
    else:
        print("✅ No hay valores faltantes")
    
    print(f"\n🔧 PREPARANDO DATOS PARA GUARDAR")
    print("=" * 50)
    df = fix_mixed_types(df)
    print("✅ Tipos de datos estandarizados")
    
    print(f"\n💾 GUARDANDO RESULTADOS")
    print("=" * 50)
    
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("reports/cross").mkdir(parents=True, exist_ok=True)
    
    df.to_parquet("data/processed/base_clean.parquet", index=False)
    print("✅ data/processed/base_clean.parquet")
    
    df.to_csv("data/processed/base_clean.csv", index=False)
    print("✅ data/processed/base_clean.csv")
    
    loc_counts.to_csv("reports/cross/localidades.csv")
    upz_counts.to_csv("reports/cross/upz.csv")
    print("✅ reports/cross/localidades.csv")
    print("✅ reports/cross/upz.csv")
    
    with open("reports/data_summary.txt", "w", encoding="utf-8") as f:
        f.write("RESUMEN DE DATOS NNA\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total registros: {len(df):,}\n")
        f.write(f"Total columnas: {df.shape[1]}\n")
        f.write(f"Localidades únicas: {df['localidad'].nunique()}\n")
        f.write(f"UPZ únicas: {df['upz'].nunique()}\n\n")
        f.write("Top 10 Localidades:\n")
        for loc, count in loc_counts.head(10).items():
            f.write(f"  - {loc}: {count:,}\n")
    
    print("✅ reports/data_summary.txt")
    print("\n🎉 ¡Análisis completado exitosamente!")
    print(f"\n📊 Resumen:")
    print(f"   • {len(df):,} registros procesados")
    print(f"   • {df.shape[1]} variables")
    print(f"   • {df['localidad'].nunique()} localidades")
    print(f"   • {df['upz'].nunique()} UPZ")

if __name__ == "__main__":
    main()
