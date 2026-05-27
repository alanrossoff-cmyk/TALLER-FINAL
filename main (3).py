"""
main.py — Orquestador principal de Dolar-Track
Universidad de La Sabana | Programación y Decisiones 2026-1

Secuencia de arranque:
  1. Inicializa la base de datos SQLite (crea tablas + datos semilla si no existen).
  2. Lanza la interfaz gráfica Tkinter.
"""

import sys
import os

# Agregar la raíz del proyecto al path para que los imports relativos funcionen
sys.path.insert(0, os.path.dirname(__file__))

from Backend.database import Database
from Frontend.gui import iniciar_app


def main():
    print("=" * 60)
    print("  📊 DOLAR-TRACK — Sistema de Análisis de TRM")
    print("  Universidad de La Sabana | Programación y Decisiones")
    print("=" * 60)

    # 1. Inicializar base de datos
    print("\n[1/2] Inicializando base de datos SQLite...")
    try:
        db = Database()
        print("      ✅ Base de datos lista:", db.db_path)
    except Exception as e:
        print(f"      ❌ Error al inicializar la base de datos: {e}")
        sys.exit(1)

    # 2. Lanzar interfaz gráfica
    print("[2/2] Lanzando interfaz gráfica...")
    print("      (Cierre la ventana para terminar el programa)\n")
    try:
        iniciar_app()
    except Exception as e:
        print(f"❌ Error en la interfaz gráfica: {e}")
        sys.exit(1)

    print("\n✅ Dolar-Track cerrado correctamente.")


if __name__ == "__main__":
    main()
