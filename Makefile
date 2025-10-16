env:
\tpython -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
E1:
\tpython src/01_data_understanding.py --input data/raw/Data_Limpia.xlsx --sheet BD
E2:
\tpython src/02_target_trabaja.py
E3:
\tpython src/03_factores.py
E4:
\tpython src/04_cluster.py
E5:
\tpython src/05_prevalencias.py
app:
\tstreamlit run src/app_streamlit.py
all: E1 E2 E3 E4 E5
