"""
cartes.py
Génération de la carte d'abonné PDF (format carte bancaire, fond bleu).
"""

import os
import sys
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from .db import get_connection
from .parametres import get_parametre

if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOSSIER_CARTES = os.path.join(_BASE, "cartes")

# Dimensions de la carte (×2 carte bancaire, format paysage)
CARD_W = 171 * mm
CARD_H = 108 * mm

# Palette
BLEU     = colors.HexColor("#1a4a8a")
BLEU2    = colors.HexColor("#1e5299")
VERT     = colors.HexColor("#2ecc71")
VERT_S   = colors.HexColor("#27ae60")
BLANC    = colors.white
BLEU_L   = colors.HexColor("#a8d8ff")
ORANGE   = colors.HexColor("#f39c12")
GRIS     = colors.HexColor("#718096")
BLANC_12 = colors.Color(1, 1, 1, 0.12)
BLANC_05 = colors.Color(1, 1, 1, 0.05)


def _fmt_date(d):
    try:
        p = d.split("-")
        return f"{p[2]}/{p[1]}/{p[0]}"
    except Exception:
        return d or "—"


def _recuperer_donnees(abonnement_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT a.id, a.date_debut, a.date_fin, a.statut, "
            "       l.nom, l.prenom, l.telephone, l.photo, "
            "       t.nom AS type_nom "
            "FROM Abonnements a "
            "JOIN Lecteurs l ON l.id = a.lecteur_id "
            "JOIN TypesAbonnement t ON t.id = a.type_abonnement_id "
            "WHERE a.id = ?",
            (abonnement_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise ValueError(f"Abonnement {abonnement_id} introuvable")
    return dict(row)


def _draw_card(c, x0, y0, donnees, nom_bib):
    """Dessine la carte complète en coordonnées canvas."""
    W, H = CARD_W, CARD_H
    R = 7 * mm

    nom_complet = f"{donnees['nom']} {donnees.get('prenom') or ''}".strip()
    telephone   = donnees.get("telephone") or "—"
    type_nom    = donnees.get("type_nom", "—")
    statut      = (donnees.get("statut") or "actif").upper()
    num_membre  = f"ABO-{donnees['id']:05d}"

    statut_couleur = VERT if statut == "ACTIF" else ORANGE if statut == "EXPIRE" else GRIS

    # ─── Fond bleu ───────────────────────────────────────
    c.setFillColor(BLEU)
    c.roundRect(x0, y0, W, H, radius=R, stroke=0, fill=1)

    # ─── Cercles décoratifs (fond) ────────────────────────
    c.setFillColor(BLANC_05)
    c.circle(x0 + W - 22*mm, y0 + H - 18*mm, 32*mm, stroke=0, fill=1)
    c.circle(x0 + W - 10*mm, y0 + 12*mm,     26*mm, stroke=0, fill=1)
    c.setFillColor(BLANC_12)
    c.circle(x0 + W - 22*mm, y0 + H - 18*mm, 20*mm, stroke=0, fill=1)

    # ─── Bande verte en haut ─────────────────────────────
    c.setFillColor(VERT)
    c.rect(x0, y0 + H - 5*mm, W, 5*mm, stroke=0, fill=1)

    # ─── Nom bibliothèque (header) ────────────────────────
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 6.5)
    c.drawString(x0 + 6*mm, y0 + H - 14*mm, "BIBLIOTHÈQUE")

    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x0 + 6*mm, y0 + H - 22*mm, nom_bib)

    # ─── Ligne de séparation sous le header ─────────────
    c.setStrokeColor(colors.Color(1, 1, 1, 0.18))
    c.setLineWidth(0.5)
    c.line(x0 + 6*mm, y0 + H - 27*mm, x0 + W - 6*mm, y0 + H - 27*mm)

    # ─── Badge statut (top right) ────────────────────────
    bx = x0 + W - 24*mm
    by = y0 + H - 22*mm
    c.setFillColor(colors.Color(
        statut_couleur.red, statut_couleur.green, statut_couleur.blue, 0.22
    ))
    c.roundRect(bx, by, 18*mm, 6*mm, radius=3*mm, stroke=0, fill=1)
    c.setStrokeColor(statut_couleur)
    c.setLineWidth(0.6)
    c.roundRect(bx, by, 18*mm, 6*mm, radius=3*mm, stroke=1, fill=0)
    c.setFillColor(statut_couleur)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(bx + 9*mm, by + 1.8*mm, statut)

    # ─── Zone photo (gauche du contenu) ──────────────────
    PH_X = x0 + 6*mm
    PH_Y = y0 + 20*mm
    PH_W = 45*mm
    PH_H = 56*mm

    photo_path = donnees.get("photo")
    photo_ok = bool(photo_path and os.path.isfile(str(photo_path)))

    if photo_ok:
        try:
            c.drawImage(
                photo_path, PH_X, PH_Y, PH_W, PH_H,
                preserveAspectRatio=True, mask="auto"
            )
            # Cadre sur la photo
            c.setStrokeColor(colors.Color(1, 1, 1, 0.35))
            c.setLineWidth(1)
            c.roundRect(PH_X, PH_Y, PH_W, PH_H, radius=3*mm, stroke=1, fill=0)
        except Exception:
            photo_ok = False

    if not photo_ok:
        # Placeholder
        c.setFillColor(colors.Color(1, 1, 1, 0.10))
        c.roundRect(PH_X, PH_Y, PH_W, PH_H, radius=3*mm, stroke=0, fill=1)
        c.setStrokeColor(colors.Color(1, 1, 1, 0.25))
        c.setLineWidth(0.8)
        c.roundRect(PH_X, PH_Y, PH_W, PH_H, radius=3*mm, stroke=1, fill=0)
        # Icône silhouette simplifiée
        cx_icon = PH_X + PH_W / 2
        cy_icon = PH_Y + PH_H / 2 + 5*mm
        c.setFillColor(colors.Color(1, 1, 1, 0.25))
        c.circle(cx_icon, cy_icon, 10*mm, stroke=0, fill=1)
        c.rect(cx_icon - 14*mm, PH_Y + 3*mm, 28*mm, 18*mm, stroke=0, fill=1)
        c.setFillColor(colors.Color(1, 1, 1, 0.30))
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx_icon, PH_Y + 2*mm, "Photo")

    # ─── Infos membre (droite du contenu) ────────────────
    IX = x0 + 58*mm
    IY = y0 + H - 32*mm  # départ depuis le haut du contenu

    # Nom complet
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 7)
    c.drawString(IX, IY, "NOM COMPLET")
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(IX, IY - 9*mm, nom_complet)

    # Téléphone
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 7)
    c.drawString(IX, IY - 18*mm, "TÉLÉPHONE")
    c.setFillColor(colors.Color(1, 1, 1, 0.88))
    c.setFont("Helvetica", 11)
    c.drawString(IX, IY - 26*mm, telephone)

    # Formule
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 7)
    c.drawString(IX, IY - 35*mm, "FORMULE")
    c.setFillColor(VERT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(IX, IY - 43*mm, type_nom)

    # ─── Séparateur avant footer ─────────────────────────
    c.setStrokeColor(colors.Color(1, 1, 1, 0.15))
    c.setLineWidth(0.5)
    c.line(x0 + 6*mm, y0 + 18*mm, x0 + W - 6*mm, y0 + 18*mm)

    # ─── Footer : dates + numéro ─────────────────────────
    FY = y0 + 5*mm

    # Début
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 6.5)
    c.drawString(x0 + 6*mm, FY + 8*mm, "DÉBUT")
    c.setFillColor(BLANC)
    c.setFont("Helvetica", 9)
    c.drawString(x0 + 6*mm, FY, _fmt_date(donnees.get("date_debut", "")))

    # Fin
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 6.5)
    c.drawString(x0 + 40*mm, FY + 8*mm, "FIN")
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x0 + 40*mm, FY, _fmt_date(donnees.get("date_fin", "")))

    # N° Membre
    c.setFillColor(BLEU_L)
    c.setFont("Helvetica", 6.5)
    c.drawRightString(x0 + W - 6*mm, FY + 8*mm, "N° MEMBRE")
    c.setFillColor(colors.Color(1, 1, 1, 0.65))
    c.setFont("Courier-Bold", 9)
    c.drawRightString(x0 + W - 6*mm, FY, num_membre)


def generer_carte_pdf(abonnement_id):
    """Génère la carte d'abonné PDF. Retourne le chemin du fichier."""
    donnees = _recuperer_donnees(abonnement_id)
    os.makedirs(DOSSIER_CARTES, exist_ok=True)

    nom_bib = get_parametre("nom_bibliotheque", "Bibliothèque")
    chemin_pdf = os.path.join(DOSSIER_CARTES, f"carte_ABO-{abonnement_id:05d}.pdf")

    PAGE_W, PAGE_H = A4
    x0 = (PAGE_W - CARD_W) / 2
    y0 = PAGE_H - 28*mm - CARD_H  # centrée en haut de page

    c = rl_canvas.Canvas(chemin_pdf, pagesize=A4)

    _draw_card(c, x0, y0, donnees, nom_bib)

    # Indication de découpe
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_W / 2, y0 - 8*mm,
                        "Découpez le long du bord de la carte  ·  Format : 85,6 × 54 mm (×2)")

    c.save()
    return chemin_pdf
