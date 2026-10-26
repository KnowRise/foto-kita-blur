PYTHON ?= python3
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
STAMP := $(VENV)/.installed

.PHONY: help venv install run clean reset

help:
	@echo "Foto Kita Blur - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make venv      Buat virtual environment (.venv) jika belum ada"
	@echo "  make install   Install/update dependencies"
	@echo "  make run       Jalankan aplikasi Foto Kita Blur"
	@echo "  make clean     Hapus __pycache__ dan file cache"
	@echo "  make reset     Hapus .venv dan cache"
	@echo ""
	@echo "Kontrol:"
	@echo "  Tunjukkan PEACE untuk blur"
	@echo "  D = toggle landmark"
	@echo "  M = mute/unmute musik"
	@echo "  ESC = keluar"
	@echo ""
	@echo "Catatan: taruh music.mp3 di root folder untuk musik (opsional)."

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)

$(STAMP): requirements.txt | venv
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@touch $(STAMP)

install: $(STAMP)

run: install
	@echo "Menjalankan Foto Kita Blur..."
	$(VENV_PY) foto_blur.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	find . -type f -name "*.pyo" -delete 2>/dev/null; true
	find . -type f -name "*~" -delete 2>/dev/null; true
	@echo "Bersih."

reset: clean
	rm -rf $(VENV)
	@echo "Venv dihapus. Jalankan 'make install' untuk setup ulang."
