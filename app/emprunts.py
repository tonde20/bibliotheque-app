"""
emprunts.py
Sortie et retour des livres : calcul automatique du retard,
de la pénalité et du total dû.
"""

from datetime import date, timedelta
from .db import get_connection
from .parametres import get_penalite_par_jour, get_duree_emprunt_defaut


def sortir_livre(livre_id, lecteur_id, duree_jours=None, date_sortie=None):
    """Enregistre la sortie d'un livre. Refuse si le livre n'est pas disponible."""
    conn = get_connection()
    livre = conn.execute("SELECT * FROM Livres WHERE id = ?", (livre_id,)).fetchone()
    if not livre:
        conn.close()
        raise ValueError(f"Livre {livre_id} introuvable")
    if livre["quantite_disponible"] <= 0:
        conn.close()
        raise ValueError(f"Le livre '{livre['titre']}' n'a plus d'exemplaire disponible.")

    # Vérifier que le lecteur a un abonnement actif
    abo_actif = conn.execute(
        "SELECT id FROM Abonnements WHERE lecteur_id = ? AND statut = 'actif' AND date_fin >= ?",
        (lecteur_id, date.today().isoformat())
    ).fetchone()
    if not abo_actif:
        lecteur = conn.execute("SELECT nom, prenom FROM Lecteurs WHERE id = ?", (lecteur_id,)).fetchone()
        nom = f"{lecteur['nom']} {lecteur['prenom'] or ''}".strip() if lecteur else f"ID {lecteur_id}"
        conn.close()
        raise ValueError(f"« {nom} » n'a pas d'abonnement actif. Veuillez l'abonner avant d'emprunter.")

    duree = duree_jours if duree_jours is not None else get_duree_emprunt_defaut()
    aujourd_hui = date.fromisoformat(date_sortie) if date_sortie else date.today()
    retour_prevu = aujourd_hui + timedelta(days=duree)

    cur = conn.execute(
        "INSERT INTO Emprunts (livre_id, lecteur_id, date_sortie, date_retour_prevue) "
        "VALUES (?, ?, ?, ?)",
        (livre_id, lecteur_id, aujourd_hui.isoformat(), retour_prevu.isoformat()),
    )
    conn.execute(
        "UPDATE Livres SET quantite_disponible = quantite_disponible - 1, "
        "statut = CASE WHEN quantite_disponible - 1 <= 0 THEN 'sorti' ELSE 'disponible' END "
        "WHERE id = ?",
        (livre_id,),
    )
    conn.commit()
    emprunt_id = cur.lastrowid
    conn.close()
    return {"emprunt_id": emprunt_id, "date_retour_prevue": retour_prevu.isoformat()}


def retourner_livre(emprunt_id, date_retour=None):
    """Enregistre le retour d'un livre, calcule le retard, la pénalité et le total."""
    conn = get_connection()
    emprunt = conn.execute("SELECT * FROM Emprunts WHERE id = ?", (emprunt_id,)).fetchone()
    if not emprunt:
        conn.close()
        raise ValueError(f"Emprunt {emprunt_id} introuvable")
    if emprunt["statut"] != "en_cours":
        conn.close()
        raise ValueError("Cet emprunt a déjà été clôturé")

    retour = date.fromisoformat(date_retour) if date_retour else date.today()
    prevue = date.fromisoformat(emprunt["date_retour_prevue"])
    jours_retard = max(0, (retour - prevue).days)
    penalite = jours_retard * get_penalite_par_jour()
    statut = "rendu_en_retard" if jours_retard > 0 else "rendu"

    conn.execute(
        "UPDATE Emprunts SET date_retour_reelle = ?, statut = ?, jours_retard = ?, "
        "penalite = ?, total = ? WHERE id = ?",
        (retour.isoformat(), statut, jours_retard, penalite, penalite, emprunt_id),
    )
    conn.execute(
        "UPDATE Livres SET quantite_disponible = quantite_disponible + 1, statut = 'disponible' "
        "WHERE id = ?",
        (emprunt["livre_id"],),
    )
    conn.commit()
    conn.close()

    if penalite > 0:
        from .tresorerie import enregistrer
        enregistrer("penalite", penalite, reference=f"Emprunt #{emprunt_id}",
                    lecteur_id=emprunt["lecteur_id"],
                    note=f"{jours_retard} jour(s) de retard", date=retour.isoformat())

    return {
        "jours_retard": jours_retard,
        "penalite": penalite,
        "total": penalite,
        "statut": statut,
    }


def calculer_retard_courant(emprunt_id):
    """Pour un emprunt encore en cours (livre pas encore rendu), calcule le
    retard 'au jour d'aujourd'hui' — utile pour l'affichage avant le retour."""
    conn = get_connection()
    emprunt = conn.execute("SELECT * FROM Emprunts WHERE id = ?", (emprunt_id,)).fetchone()
    conn.close()
    if not emprunt or emprunt["statut"] != "en_cours":
        return 0
    prevue = date.fromisoformat(emprunt["date_retour_prevue"])
    return max(0, (date.today() - prevue).days)


def lister_emprunts_en_cours():
    conn = get_connection()
    rows = conn.execute(
        "SELECT e.*, l.titre AS livre_titre, c.nom AS lecteur_nom, c.prenom AS lecteur_prenom "
        "FROM Emprunts e "
        "JOIN Livres l ON l.id = e.livre_id "
        "JOIN Lecteurs c ON c.id = e.lecteur_id "
        "WHERE e.statut = 'en_cours' ORDER BY e.date_retour_prevue",
    ).fetchall()
    conn.close()
    resultat = []
    for r in rows:
        d = dict(r)
        d["jours_retard_actuel"] = max(0, (date.today() - date.fromisoformat(d["date_retour_prevue"])).days)
        d["en_retard"] = d["jours_retard_actuel"] > 0
        resultat.append(d)
    return resultat


def lister_historique_lecteur(lecteur_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT e.*, l.titre AS livre_titre FROM Emprunts e "
        "JOIN Livres l ON l.id = e.livre_id "
        "WHERE e.lecteur_id = ? ORDER BY e.date_sortie DESC",
        (lecteur_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
