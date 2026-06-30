"""
abonnements.py
Souscription d'un abonnement, calcul de sa date de fin,
et émission du reçu correspondant (sans le PDF pour l'instant —
le PDF sera ajouté à l'étape suivante avec ReportLab).
"""

from datetime import date, timedelta
from .db import get_connection


def lister_types_abonnement():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM TypesAbonnement ORDER BY duree_jours").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _generer_numero_recu(conn):
    """Génère un numéro du type REC-2026-00001, incrémental par année."""
    annee = date.today().year
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(numero_recu, -5) AS INTEGER)) AS max_n "
        "FROM Recus WHERE numero_recu LIKE ?", (f"REC-{annee}-%",)
    ).fetchone()
    max_n = row["max_n"] or 0
    return f"REC-{annee}-{max_n + 1:05d}"


def creer_abonnement(lecteur_id, type_abonnement_id, montant_paye=None, date_debut=None, generer_pdf=True, duree_jours_override=None):
    """
    Crée l'abonnement, calcule sa date de fin à partir de la durée du type
    choisi, et émet immédiatement le reçu correspondant (ligne en base).
    Si generer_pdf=True (par défaut), génère aussi le fichier PDF du reçu.
    Retourne un dict avec les infos de l'abonnement ET du reçu.
    """
    conn = get_connection()
    try:
        type_abo = conn.execute(
            "SELECT * FROM TypesAbonnement WHERE id = ?", (type_abonnement_id,)
        ).fetchone()
        if not type_abo:
            raise ValueError(f"Type d'abonnement {type_abonnement_id} introuvable")

        debut = date.fromisoformat(date_debut) if date_debut else date.today()
        duree = duree_jours_override if duree_jours_override is not None else type_abo["duree_jours"]
        fin = debut + timedelta(days=duree)
        montant = montant_paye if montant_paye is not None else type_abo["prix"]
        nom_type = type_abo["nom"]

        cur = conn.execute(
            "INSERT INTO Abonnements (lecteur_id, type_abonnement_id, date_debut, date_fin, montant_paye) "
            "VALUES (?, ?, ?, ?, ?)",
            (lecteur_id, type_abonnement_id, debut.isoformat(), fin.isoformat(), montant),
        )
        abonnement_id = cur.lastrowid

        numero_recu = _generer_numero_recu(conn)
        conn.execute(
            "INSERT INTO Recus (abonnement_id, numero_recu, montant, duree_jours) VALUES (?, ?, ?, ?)",
            (abonnement_id, numero_recu, montant, duree),
        )
        conn.commit()
    finally:
        conn.close()

    resultat = {
        "abonnement_id": abonnement_id,
        "numero_recu": numero_recu,
        "date_debut": debut.isoformat(),
        "date_fin": fin.isoformat(),
        "duree_jours": duree,
        "montant": montant,
        "chemin_pdf": None,
    }

    if generer_pdf:
        from .recus import generer_recu_pdf
        resultat["chemin_pdf"] = generer_recu_pdf(abonnement_id)
        try:
            from .cartes import generer_carte_pdf
            resultat["chemin_carte"] = generer_carte_pdf(abonnement_id)
        except Exception:
            resultat["chemin_carte"] = None

    from .tresorerie import enregistrer
    enregistrer("abonnement", montant, reference=numero_recu, lecteur_id=lecteur_id,
                note=f"Abonnement {nom_type}", date=debut.isoformat())

    return resultat


def lister_abonnements_lecteur(lecteur_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT a.*, t.nom AS type_nom FROM Abonnements a "
        "JOIN TypesAbonnement t ON t.id = a.type_abonnement_id "
        "WHERE a.lecteur_id = ? AND a.statut != 'annule' ORDER BY a.date_debut DESC",
        (lecteur_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def annuler_abonnement(abonnement_id):
    conn = get_connection()
    # Récupérer le numéro de reçu pour supprimer l'entrée trésorerie
    recu = conn.execute(
        "SELECT numero_recu FROM Recus WHERE abonnement_id = ?", (abonnement_id,)
    ).fetchone()
    conn.execute(
        "UPDATE Abonnements SET statut = 'annule' WHERE id = ? AND statut = 'actif'",
        (abonnement_id,),
    )
    if recu:
        conn.execute(
            "DELETE FROM Tresorerie WHERE reference = ?", (recu["numero_recu"],)
        )
    conn.commit()
    conn.close()


def actualiser_statuts_abonnements():
    """À appeler régulièrement (ex: au démarrage de l'app) : passe en 'expire'
    tout abonnement actif dont la date de fin est dépassée."""
    conn = get_connection()
    conn.execute(
        "UPDATE Abonnements SET statut = 'expire' "
        "WHERE statut = 'actif' AND date_fin < ?",
        (date.today().isoformat(),),
    )
    conn.commit()
    conn.close()
