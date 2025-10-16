import numpy as np, pandas as pd, matplotlib.pyplot as plt
from sklearn_extra.cluster import KMedoids
from sklearn.metrics import silhouette_score

scores = pd.read_parquet("data/processed/factor_scores.parquet").dropna()
X = scores.filter(regex="^PC\\d+$").values

best = {"k":None,"sil":-1,"labels":None,"model":None}
sil_curve = []
for k in range(3,9):
    model = KMedoids(n_clusters=k, random_state=42, method="alternate").fit(X)
    sil = silhouette_score(X, model.labels_)
    sil_curve.append((k, sil))
    if sil>best["sil"]:
        best = {"k":k,"sil":sil,"labels":model.labels_, "model":model}

# guarda asignación
out = scores[["row_id"]].copy()
out["cluster"] = best["labels"]
out.to_parquet("data/processed/cluster_assign.parquet", index=False)

# curva silhouette
ks, sils = zip(*sil_curve)
plt.figure(); plt.plot(ks, sils, marker="o"); plt.xlabel("k"); plt.ylabel("Silhouette")
plt.title(f"Silhouette (mejor k={best['k']}, {best['sil']:.2f})"); plt.tight_layout()
plt.savefig("reports/figures/silhouette_curve.png"); plt.close()
print(f"[E4] OK → cluster_assign.parquet (k={best['k']})")
