# 📊 Análisis de Datos NNA (Niños, Niñas y Adolescentes)

Proyecto de análisis de datos sobre trabajo infantil y adolescente en Bogotá.

## 🗂️ Estructura del Proyecto
```
NNA_7/
├── data/
│   ├── raw/              # Datos originales (Excel)
│   └── processed/        # Datos procesados (Parquet)
├── src/                  # Scripts de análisis
│   ├── 01_data_understanding.py
│   ├── 02_target_engineering.py
│   ├── 03_factor_analysis.py
│   └── 04_clustering.py
├── reports/              # Resultados y reportes
│   ├── figures/          # Gráficos generados
│   └── cross/            # Tablas cruzadas
└── README.md
```

## 🚀 Uso

### 1. Preparar datos
Coloca tus archivos Excel en `data/raw/`

### 2. Ejecutar pipeline completo
```bash
python src/01_data_understanding.py
python src/02_target_engineering.py
python src/03_factor_analysis.py
python src/04_clustering.py
```

## 📋 Descripción de Scripts

### 01_data_understanding.py
- Carga y limpia datos desde Excel
- Análisis exploratorio inicial
- Genera estadísticas descriptivas por territorio y demografía

### 02_target_engineering.py
- Construye variable objetivo: "trabaja" (Sí/No)
- Usa múltiples fuentes: trabajo explícito, protegido, desvinculación
- Genera reporte de decisiones

### 03_factor_analysis.py
- Análisis de componentes principales (PCA)
- Codifica variables categóricas
- Reduce dimensionalidad del dataset

### 04_clustering.py
- Clustering K-Medoids/K-Means
- Agrupa NNA según características similares
- Selección óptima de clusters por Silhouette

## 📊 Outputs

### Datos procesados
- `data/processed/base_clean.parquet` - Dataset limpio
- `data/processed/target_trabaja.parquet` - Variable objetivo
- `data/processed/factor_scores.parquet` - Scores factoriales
- `data/processed/cluster_assign.parquet` - Asignación de clusters

### Reportes
- `reports/data_summary.txt`
- `reports/target_engineering_report.txt`
- `reports/pca_report.txt`
- `reports/clustering_report.txt`

### Visualizaciones
- `reports/figures/scree_pca.png`
- `reports/figures/biplot_pca.png`
- `reports/figures/clustering_analysis.png`
- `reports/figures/clusters_2d.png`

## 🛠️ Requisitos
```bash
pip install pandas numpy matplotlib seaborn scikit-learn pyarrow openpyxl
```

## Autores

Angela Rico 
Carlos Diaz
Diego Gomez

## 📝 Licencia

Este proyecto es para fines académicos y de investigación.
