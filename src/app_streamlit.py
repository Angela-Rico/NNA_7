import streamlit as st, pandas as pd

st.title("NNA Bogotá — Perfiles y Prevalencias")

base  = pd.read_parquet("data/processed/base_clean.parquet")
y     = pd.read_parquet("data/processed/target_trabaja.parquet")
clus  = pd.read_parquet("data/processed/cluster_assign.parquet")
df = base.merge(y, on="row_id", how="left").merge(clus, on="row_id", how="left")

periodos = sorted([p for p in df["periodo"].dropna().unique()])
k = int(df["cluster"].max()+1) if "cluster" in df else 0

p_sel = st.selectbox("Periodo", periodos) if periodos else None
st.write(f"k = {k}" if k else "Clusters aún no generados")

if p_sel:
    tmp = df[df["periodo"]==p_sel]
    st.write("Prevalencia por cluster")
    st.dataframe(tmp.groupby("cluster")["trabaja"].mean().to_frame("p_hat"))
