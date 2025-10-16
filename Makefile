env:
\tpython -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
E1:
python src/01_data_understanding.py --input data/raw/Data_Limpia.xlsx  # toma la 1ª hoja
E2:
\tpython src/02_target_trabaja.py
E3:
\tpython src/03_factores.py
E4:
\tpython src/04_cluster.py
all: E1 E2 E3 E4
