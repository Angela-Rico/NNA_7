import numpy as np, pandas as pd
from math import sqrt

def wilson(p, n, z=1.96):
    if n==0: return (np.nan,np.nan,np.nan)
    denom = 1 + z**2/n
    center = (p + z**2/(2*n))/denom
    half = z*sqrt((p*(1-p)+z**2/(4*n))/n)/denom
    return (center, max(0, center-half), min(1, center+half))

base   = pd.read_parquet("data/processed/base_clean.parquet")[["row_id","periodo","localidad","upz"]]
y      = pd.read_parquet("data/processed/target_trabaja.parquet")
clust  = pd.read_parquet("data/processed/cluster_assign.parquet")

df = base.merge(y, on="row_id", how="left").merge(clust, on="row_id", how="left")
df["trabaja"] = df["trabaja"].astype("float")

# por periodo×cluster
g1 = (df.dropna(subset=["cluster","periodo"])
        .groupby(["periodo","cluster"])["trabaja"]
        .agg(n="count", ysum="sum"))
g1["p"] = g1["ysum"]/g1["n"]
g1["p_hat"], g1["lwr"], g1["upr"] = zip(*g1.apply(lambda r: wilson(r["p"], r["n"]), axis=1))
g1.to_csv("reports/prevalencias_periodo_cluster.csv")

# por periodo×territorio×cluster (UPZ si existe, si no Localidad)
territ = "upz" if "upz" in df.columns else "localidad"
g2 = (df.dropna(subset=["cluster","periodo"])
        .groupby(["periodo",territ,"cluster"])["trabaja"]
        .agg(n="count", ysum="sum"))
g2["p"] = g2["ysum"]/g2["n"]
g2["p_hat"], g2["lwr"], g2["upr"] = zip(*g2.apply(lambda r: wilson(r["p"], r["n"]), axis=1))
# marca n<30
g2["publicable"] = g2["n"]>=30
g2.to_csv("reports/prevalencias_periodo_territorio_cluster.csv")
print("[E5] OK → prevalencias*.csv")
