.PHONY: all install clean run upload help

# Variables
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m

all: install run
	@echo "$(GREEN)✅ Pipeline completo ejecutado$(NC)"

# Crear entorno virtual e instalar dependencias
install:
	@echo "$(YELLOW)📦 Instalando dependencias...$(NC)"
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Instalación completa$(NC)"

# Ejecutar pipeline completo
run: E1 E2 E3 E4
	@echo "$(GREEN)✅ Todos los scripts ejecutados$(NC)"

E1:
	@echo "$(YELLOW)📊 Ejecutando análisis exploratorio...$(NC)"
	$(PYTHON) src/01_data_understanding.py

E2:
	@echo "$(YELLOW)🎯 Construyendo variable objetivo...$(NC)"
	$(PYTHON) src/02_target_engineering.py

E3:
	@echo "$(YELLOW)🔬 Análisis factorial (PCA)...$(NC)"
	$(PYTHON) src/03_factor_analysis.py

E4:
	@echo "$(YELLOW)🎯 Clustering...$(NC)"
	$(PYTHON) src/04_clustering.py

# Limpiar archivos generados
clean:
	@echo "$(YELLOW)🧹 Limpiando archivos generados...$(NC)"
	rm -rf $(VENV)
	rm -rf __pycache__ src/__pycache__
	rm -rf data/processed/*
	rm -rf reports/figures/*
	rm -rf reports/cross/*
	rm -rf reports/*.txt reports/*.csv
	@echo "$(GREEN)✅ Limpieza completa$(NC)"

# Subir todo a GitHub
upload:
	@echo "$(YELLOW)📤 Subiendo a GitHub...$(NC)"
	git add -A
	@read -p "Mensaje del commit: " msg; \
	git commit -m "$$msg"
	git push origin main
	@echo "$(GREEN)✅ Subido a GitHub$(NC)"

# Subir cambios rápido (con mensaje automático)
quick-upload:
	@echo "$(YELLOW)⚡ Subida rápida...$(NC)"
	git add -A
	git commit -m "🔄 Actualización: $$(date '+%Y-%m-%d %H:%M')"
	git push origin main
	@echo "$(GREEN)✅ Cambios subidos$(NC)"

# Ayuda
help:
	@echo "$(GREEN)🚀 Makefile - Proyecto NNA_7$(NC)"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar dependencias"
	@echo "  make run          - Ejecutar pipeline completo"
	@echo "  make E1           - Solo análisis exploratorio"
	@echo "  make E2           - Solo ingeniería de target"
	@echo "  make E3           - Solo análisis factorial"
	@echo "  make E4           - Solo clustering"
	@echo "  make clean        - Limpiar archivos generados"
	@echo "  make upload       - Subir cambios a GitHub (con mensaje)"
	@echo "  make quick-upload - Subir rápido (mensaje automático)"
	@echo "  make all          - Instalar y ejecutar todo"
	@echo "  make help         - Mostrar esta ayuda"
