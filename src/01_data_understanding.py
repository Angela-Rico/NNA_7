#!/usr/bin/env python
import os, re, json, argparse
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

PII_PAT = re.compile(r'(nombre|apellido|documento|direccion|tel|cel|correo|email)', re.I)
NA_CODES = {99999, 98, 99, "98", "99", "99999", "", "NA", "N/A", None}

def ensure_dirs():
    for d in ["reports","reports/figures","reports/cross","data/processed"]:
        os.makedirs(d, exist_ok=True)

def normalize_cols(df):
    cols = (df.columns
            .str.strip().str.replace(r"\s+", " ", regex=True)
            .str.lower().str.replace(" ", "_"))
    out = df.copy(); out.columns = cols; return out

def drop_pii(df):
    keep = [c for c in df.columns if not PII_PAT.search(c)]
    return df[keep]

def recode_na(df):
    return df.applymap(lambda x: (np.nan if (pd.isna(x) or x in NA_CODES) else x))

def plot_missing(df, out_png):
    miss = df.isna().mean().sort_values(ascending=False).head(50)
    plt.figure(); miss.plot(kind="bar"); plt.title("Faltantes por columna")
    plt.ylabel("Proporción"); plt.tight_layout(); plt.savefig(out_png); plt.close()

def plot_corr(df, out_png):
    num = df.select_dtypes(include=[np.number])
    if num.shape[1] < 2: return
    corr = num.corr(numeric_only=True)
    plt.figure(); plt.imshow(corr.values, interpolation="nearest")
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
    plt.yticks(range(len(corr.columns)), corr.columns)
    plt.title("Matriz de correlación"); plt.colorbar(); plt.tight_layout()
    plt.savefig(out_png); plt.close()

def infer_period(df):
    fecha_cols = [c for c in df.columns if "fecha" in c]
    if not fecha_cols: return df
    fc = fecha_cols[0]
    dts = pd.to_datetime(df[fc], errors="coerce")
    df["periodo"] = dts.dt.to_period("M").astype(str)
    return df

def infer_territorio(df):
    if "localidad" not in df.columns:
        cand = [c for c in df.columns if "localidad" in c]
        if cand: df = df.rename(columns={cand[0]: "localidad"})
    if "upz" not in df.columns:
        cand = [c for c in df.columns if c.startswith("upz")]
        if cand: df = df.rename(columns={cand[0]: "upz"})
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--sheet", default=None)
    args = ap.parse_args()
    ensure_dirs()

    # carga
    if args.input.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(args.input, sheet_name=args.sheet)
    else:
        df = pd.read_csv(args.input)

    # limpieza base
    df = normalize_cols(df)
    df = recode_na(df)
    df = drop_pii(df)

    # filtro 5–17 si existe edad*
    edad_col = next((c for c in df.columns if c.startswith("edad")), None)
    if edad_col is not None:
        df[edad_col] = pd.to_numeric(df[edad_col], errors="coerce")
        df = df[df[edad_col].between(5,17)]

    # id estable
    df = df.reset_index(drop=True)
    df.insert(0, "row_id", df.index.astype(int))

    # extras útiles
    df = infer_period(df)
    df = infer_territorio(df)

    # diccionario + calidad
    dd = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "non_null": df.notna().sum().values,
        "nulls": df.isna().sum().values,
        "null_pct": (df.isna().mean().values*100).round(2),
        "n_unique": df.nunique(dropna=True).values
    })
    dd.to_csv("reports/data_dictionary.csv", index=False)

    flags = {
        "rows": int(df.shape[0]), "cols": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "constant_like": [c for c in df.columns
                          if (df[c].value_counts(normalize=True, dropna=True).head(1).sum()>=0.99)],
        "candidate_ids": [c for c in df.columns if df[c].is_unique]
    }
    json.dump(flags, open("reports/quality_flags.json","w"), ensure_ascii=False, indent=2)

    # gráficos rápidos
    plot_missing(df, "reports/figures/missing_bar.png")
    plot_corr(df, "reports/figures/corr_matrix.png")

    # guarda base limpia
    df.to_parquet("data/processed/base_clean.parquet", index=False)
    print("[E1] OK → data/processed/base_clean.parquet")

if __name__ == "__main__":
    main()
