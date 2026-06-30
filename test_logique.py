"""
test_logique.py
Exerce toute la logique métier sans interface graphique.
À lancer depuis le dossier du projet : python test_logique.py
"""

import os
from datetime import date, timedelta

from app import livres, lecteurs, abonnements, emprunts
from app.db import get_connection


def remettre_a_zero():
    """Vide les tables de test pour pouvoir relancer le script plusieurs fois."""
    conn = get_connection()
    for table in ["Emprunts", "Recus", "Abonnements", "Livres", "Lecteurs"]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


def main():
    remettre_a_zero()
    print("== Test logique métier ==\n")

    # --- Livres ---
    id_livre1 = livres.ajouter_livre("Le Petit Prince", "Antoine de Saint-Exupéry", "001")
    id_livre2 = livres.ajouter_livre("1984", "George Orwell", "002")
    print("Livres ajoutés :", livres.lister_livres())

    # --- Lecteurs ---
    id_lecteur = lecteurs.ajouter_lecteur("Diop", "Awa", telephone="770000000")
    print("\nLecteur ajouté :", lecteurs.obtenir_lecteur(id_lecteur))

    # --- Abonnement + reçu ---
    types = abonnements.lister_types_abonnement()
    print("\nTypes d'abonnement disponibles :", types)
    abo = abonnements.creer_abonnement(id_lecteur, types[0]["id"])
    print("\nAbonnement créé, reçu émis :", abo)
    assert abo["chemin_pdf"] and os.path.exists(abo["chemin_pdf"]), "Le PDF du reçu n'a pas été créé"
    print("PDF du reçu généré avec succès :", abo["chemin_pdf"])

    # --- Sortie de livre normale ---
    sortie1 = emprunts.sortir_livre(id_livre1, id_lecteur, duree_jours=14)
    print("\nSortie livre 1 :", sortie1)
    print("Statut livre 1 après sortie :", livres.lister_livres()[0]["statut"])

    # --- Retour à temps ---
    retour1 = emprunts.retourner_livre(sortie1["emprunt_id"])
    print("\nRetour livre 1 (à temps) :", retour1)

    # --- Sortie + retour EN RETARD (on simule une sortie il y a 20 jours, due dans 14j) ---
    conn = get_connection()
    date_sortie_passee = (date.today() - timedelta(days=20)).isoformat()
    date_retour_prevue_passee = (date.today() - timedelta(days=6)).isoformat()
    conn.execute(
        "INSERT INTO Emprunts (livre_id, lecteur_id, date_sortie, date_retour_prevue) VALUES (?, ?, ?, ?)",
        (id_livre2, id_lecteur, date_sortie_passee, date_retour_prevue_passee),
    )
    conn.execute("UPDATE Livres SET statut = 'sorti' WHERE id = ?", (id_livre2,))
    conn.commit()
    emprunt_retard_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()

    print("\nRetard courant avant retour (devrait être 6) :", emprunts.calculer_retard_courant(emprunt_retard_id))
    print("Emprunts en cours :", emprunts.lister_emprunts_en_cours())

    retour2 = emprunts.retourner_livre(emprunt_retard_id)
    print("\nRetour livre 2 (en retard) :", retour2)
    assert retour2["jours_retard"] == 6, "Le calcul de retard est incorrect"
    print("\n✔ Tous les contrôles sont passés.")


if __name__ == "__main__":
    main()
