"""
lecteurs.py
Gestion des lecteurs (abonnés) de la bibliothèque.
"""

from .db import get_connection


def ajouter_lecteur(nom, prenom=None, telephone=None, email=None, adresse=None, photo=None):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO Lecteurs (nom, prenom, telephone, email, adresse, photo) VALUES (?, ?, ?, ?, ?, ?)",
        (nom, prenom, telephone, email, adresse, photo),
    )
    conn.commit()
    lecteur_id = cur.lastrowid
    conn.close()
    return lecteur_id


def lister_lecteurs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM Lecteurs ORDER BY nom, prenom").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rechercher_lecteur(mot_cle):
    conn = get_connection()
    motif = f"%{mot_cle}%"
    rows = conn.execute(
        "SELECT * FROM Lecteurs WHERE nom LIKE ? OR prenom LIKE ? OR telephone LIKE ? ORDER BY nom",
        (motif, motif, motif),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtenir_lecteur(lecteur_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM Lecteurs WHERE id = ?", (lecteur_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def supprimer_lecteur(lecteur_id):
    from .db import get_connection
    conn = get_connection()
    try:
        # Remettre en stock les livres encore sortis par ce lecteur
        emprunts_en_cours = conn.execute(
            "SELECT livre_id FROM Emprunts WHERE lecteur_id = ? AND statut = 'en_cours'",
            (lecteur_id,)
        ).fetchall()
        for e in emprunts_en_cours:
            conn.execute(
                "UPDATE Livres SET quantite_disponible = quantite_disponible + 1, "
                "statut = 'disponible' WHERE id = ?",
                (e["livre_id"],)
            )
        # Supprimer toutes les données liées
        conn.execute("DELETE FROM Tresorerie WHERE lecteur_id = ?", (lecteur_id,))
        conn.execute("DELETE FROM Recus WHERE abonnement_id IN (SELECT id FROM Abonnements WHERE lecteur_id = ?)", (lecteur_id,))
        conn.execute("DELETE FROM Abonnements WHERE lecteur_id = ?", (lecteur_id,))
        conn.execute("DELETE FROM Emprunts WHERE lecteur_id = ?", (lecteur_id,))
        conn.execute("DELETE FROM Lecteurs WHERE id = ?", (lecteur_id,))
        conn.commit()
    finally:
        conn.close()


def modifier_lecteur(lecteur_id, **champs):
    if not champs:
        return
    colonnes = ", ".join(f"{k} = ?" for k in champs)
    valeurs = list(champs.values()) + [lecteur_id]
    conn = get_connection()
    conn.execute(f"UPDATE Lecteurs SET {colonnes} WHERE id = ?", valeurs)
    conn.commit()
    conn.close()
