import pandas as pd
import numpy as np

def map_bin(s):
    if s is None: return np.nan
    return s.map({"si":1,"sí":1,"yes":1,"1":1,1:1,
                  "no":0,"0":0,0:0}).astype("float")

df = pd.read_parquet("data/processed/base_clean.parquet")

# columnas posibles (ajusta nombres si difieren)
col_trabaja      = next((c for c in df.columns if c.endswith("trabaja")), None)
col_desvinculado = next((c for c in df.columns if "desvinculado" in c), None)
col_trab_prot    = next((c for c in df.columns if "trabajo_proteg" in c), None)

y = pd.Series(np.nan, index=df.index, dtype="float")

# 1) si existe 'trabaja' explícito, se respeta
if col_trabaja:
    y = map_bin(df[col_trabaja].astype(str).str.lower())

# 2) trabajo protegido implica trabaja=1 cuando y es NA
if col_trab_prot:
    y = y.fillna(map_bin(df[col_trab_prot].astype(str).str.lower()).replace({0:np.nan}))
    y = y.where(~y.isna(), 1.0)  # si col_trab_prot==1 y y era NA → 1

# 3) desvinculado define 0/1 cuando y es NA
if col_desvinculado:
    d = map_bin(df[col_desvinculado].astype(str).str.lower())
    y = y.fillna(1 - d)  # desvinculado=1 → trabaja=0; desvinculado=0 → 1

df["trabaja"] = y
df[["row_id","trabaja"]].to_parquet("data/processed/target_trabaja.parquet", index=False)
df[["row_id","trabaja"]].to_csv("reports/target_decisions.csv", index=False)
print("[E2] OK → target_trabaja.parquet")
