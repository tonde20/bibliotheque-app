"""
init_db.py
Crée le fichier bibliotheque.db à partir de schema.sql,
et insère les données de base (types d'abonnement, paramètres).

Usage : python init_db.py
"""

import sqlite3
import os

DB_PATH = "bibliotheque.db"
SCHEMA_PATH = "schema.sql"


def creer_base():
    if os.path.exists(DB_PATH):
        reponse = input(f"'{DB_PATH}' existe déjà. Continuer va appliquer le schéma "
                         f"dessus sans effacer les données. Continuer ? (o/n) : ")
        if reponse.lower() != "o":
            print("Annulé.")
            return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cur.executescript(f.read())

    # --- Types d'abonnement par défaut (modifiables ensuite dans l'appli) ---
    cur.execute("SELECT COUNT(*) FROM TypesAbonnement")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO TypesAbonnement (nom, duree_jours, prix) VALUES (?, ?, ?)",
            [
                ("1 semaine", 7, 500),
                ("2 semaines", 14, 900),
                ("1 mois", 30, 2000),
                ("3 mois", 90, 5000),
                ("6 mois", 180, 9000),
                ("1 an", 365, 15000),
            ],
        )

    # --- Paramètres par défaut (à ajuster selon tes tarifs réels) ---
    cur.execute("SELECT COUNT(*) FROM Parametres")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO Parametres (cle, valeur) VALUES (?, ?)",
            [
                ("penalite_par_jour_retard", "100"),       # montant par jour de retard
                ("duree_emprunt_defaut_jours", "14"),      # durée standard d'un emprunt
                ("devise", "FCFA"),
            ],
        )

    conn.commit()
    conn.close()
    print(f"Base de données créée/mise à jour : {DB_PATH}")


if __name__ == "__main__":
    creer_base()
