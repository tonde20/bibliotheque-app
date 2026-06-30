"""
livres.py
Gestion du catalogue de livres.
"""

from .db import get_connection


def ajouter_livre(titre, auteur=None, isbn=None, categorie=None, quantite=1):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO Livres (titre, auteur, isbn, categorie, quantite_total, quantite_disponible) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (titre, auteur, isbn, categorie, quantite, quantite),
    )
    conn.commit()
    livre_id = cur.lastrowid
    conn.close()
    return livre_id


def lister_livres(statut=None):
    """Si statut='disponible', retourne les livres ayant au moins un exemplaire dispo."""
    conn = get_connection()
    if statut == "disponible":
        rows = conn.execute(
            "SELECT * FROM Livres WHERE quantite_disponible > 0 ORDER BY titre"
        ).fetchall()
    elif statut:
        rows = conn.execute("SELECT * FROM Livres WHERE statut = ? ORDER BY titre", (statut,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM Livres ORDER BY titre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rechercher_livre(mot_cle):
    """Recherche simple sur le titre, l'auteur ou l'ISBN."""
    conn = get_connection()
    motif = f"%{mot_cle}%"
    rows = conn.execute(
        "SELECT * FROM Livres WHERE titre LIKE ? OR auteur LIKE ? OR isbn LIKE ? ORDER BY titre",
        (motif, motif, motif),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def modifier_livre(livre_id, **champs):
    """Met à jour les champs fournis, ex: modifier_livre(3, titre='Nouveau titre')."""
    if not champs:
        return
    colonnes = ", ".join(f"{k} = ?" for k in champs)
    valeurs = list(champs.values()) + [livre_id]
    conn = get_connection()
    conn.execute(f"UPDATE Livres SET {colonnes} WHERE id = ?", valeurs)
    conn.commit()
    conn.close()


def changer_statut_livre(livre_id, statut):
    """statut attendu : 'disponible', 'sorti', 'perdu' ou 'retire'."""
    modifier_livre(livre_id, statut=statut)


def supprimer_livre(livre_id):
    conn = get_connection()
    conn.execute("DELETE FROM Livres WHERE id = ?", (livre_id,))
    conn.commit()
    conn.close()
