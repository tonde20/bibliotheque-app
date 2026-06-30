"""
parametres.py
Lecture/écriture des réglages modifiables (pénalité de retard,
durée d'emprunt par défaut, devise) sans toucher au code.
"""

from .db import get_connection


def get_parametre(cle, defaut=None):
    conn = get_connection()
    row = conn.execute("SELECT valeur FROM Parametres WHERE cle = ?", (cle,)).fetchone()
    conn.close()
    return row["valeur"] if row else defaut


def set_parametre(cle, valeur):
    conn = get_connection()
    conn.execute(
        "INSERT INTO Parametres (cle, valeur) VALUES (?, ?) "
        "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
        (cle, str(valeur)),
    )
    conn.commit()
    conn.close()


def get_penalite_par_jour():
    return float(get_parametre("penalite_par_jour_retard", 0))


def get_duree_emprunt_defaut():
    return int(get_parametre("duree_emprunt_defaut_jours", 14))
