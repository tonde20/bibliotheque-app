"""
tresorerie.py
Enregistrement et consultation des encaissements (abonnements + pénalités).
"""

from .db import get_connection


def enregistrer(type_, montant, reference=None, lecteur_id=None, note=None, date=None):
    conn = get_connection()
    if date:
        conn.execute(
            "INSERT INTO Tresorerie (date, type, montant, reference, lecteur_id, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date, type_, montant, reference, lecteur_id, note),
        )
    else:
        conn.execute(
            "INSERT INTO Tresorerie (type, montant, reference, lecteur_id, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (type_, montant, reference, lecteur_id, note),
        )
    conn.commit()
    conn.close()


def lister(annee=None, mois=None):
    conn = get_connection()
    sql = (
        "SELECT t.*, l.nom || ' ' || COALESCE(l.prenom, '') AS lecteur_nom "
        "FROM Tresorerie t LEFT JOIN Lecteurs l ON l.id = t.lecteur_id "
    )
    params = []
    conditions = []
    if annee:
        conditions.append("strftime('%Y', t.date) = ?")
        params.append(str(annee))
    if mois:
        conditions.append("strftime('%m', t.date) = ?")
        params.append(f"{mois:02d}")
    if conditions:
        sql += "WHERE " + " AND ".join(conditions) + " "
    sql += "ORDER BY t.date DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resume(annee=None, mois=None):
    lignes = lister(annee, mois)
    total_abo = sum(l["montant"] for l in lignes if l["type"] == "abonnement")
    total_pen = sum(l["montant"] for l in lignes if l["type"] == "penalite")
    total_autre = sum(l["montant"] for l in lignes if l["type"] == "autre")
    return {
        "abonnements": total_abo,
        "penalites": total_pen,
        "autre": total_autre,
        "total": total_abo + total_pen + total_autre,
        "nb_transactions": len(lignes),
    }


def annees_disponibles():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT strftime('%Y', date) AS annee FROM Tresorerie ORDER BY annee DESC"
    ).fetchall()
    conn.close()
    return [r["annee"] for r in rows]
