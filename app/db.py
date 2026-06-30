"""
db.py
Point d'accès unique à la base SQLite. Toutes les autres modules
passent par get_connection() pour parler à bibliotheque.db.
"""

import sqlite3
import os
import sys

# En mode compilé (PyInstaller), les données sont à côté de l'exe.
# En mode développement, elles sont à la racine du projet.
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(_BASE, "bibliotheque.db")


def get_connection():
    """Ouvre une connexion avec les clés étrangères activées et les
    lignes accessibles par nom de colonne (plus pratique que par index)."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
