"""Testes de "Ajude a melhorar o DuiaOS". Rodar: python3 -m unittest discover -s relatorios/testes -t ."""
import sys
from pathlib import Path

# duiaos_registro fica em relatorios/ (no sistema, em dist-packages)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
