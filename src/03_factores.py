import pandas as pd, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

df = pd.read_parquet("data/processed/base_clean.parquet")

# selecciona numéricas para condiciones familiares/acompañamiento (ajusta si hace falta)
cand = [c for c in df.select_dtypes(include=[np.number]).columns
        if any(k in c for k in ["sisben","estrato","tam","miembros","escolar","acceso","acompan","iec","ingreso"])]

X = df[cand].dropna()
sc = StandardScaler().fit(X)
Z = sc.transform(X)

pca = PCA(n_components=min(8, Z.shape[1]))
F = pca.fit_transform(Z)

# guardar puntajes alineados a row_id
scores = pd.DataFrame(F, columns=[f"PC{i+1}" for i in range(F.shape[1])], index=X.index)
scores = scores.join(df.loc[X.index, ["row_id"]]).reset_index(drop=True)
scores.to_parquet("data/processed/factor_scores.parquet", index=False)

# cargas
loadings = pd.DataFrame(pca.components_.T, index=cand, columns=[f"PC{i+1}" for i in range(F.shape[1])])
loadings.to_csv("reports/factor_loadings.csv")

# scree
plt.figure(); plt.plot(range(1,len(pca.explained_variance_ratio_)+1),
                       pca.explained_variance_ratio_, marker="o")
plt.title("Scree"); plt.xlabel("Componente"); plt.ylabel("Var. explicada"); plt.tight_layout()
plt.savefig("reports/figures/scree_pca.png"); plt.close()
print("[E3] OK → factor_scores.parquet")
