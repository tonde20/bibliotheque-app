"""
recus.py
Génération du reçu PDF pour un abonnement, avec ReportLab.
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from .db import get_connection
from .parametres import get_parametre

if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOSSIER_RECUS = os.path.join(_BASE, "recus")

# Palette
C_BLEU      = colors.HexColor("#1a4a8a")
C_VERT      = colors.HexColor("#2ecc71")
C_VERT_S    = colors.HexColor("#27ae60")
C_BLEU_L    = colors.HexColor("#e8f0fa")
C_VERT_L    = colors.HexColor("#e8f8ee")
C_GRIS_L    = colors.HexColor("#f7fafc")
C_GRIS_BD   = colors.HexColor("#e2e8f0")
C_BLEU_BD   = colors.HexColor("#c3d8f0")
C_TEXTE     = colors.HexColor("#2d3748")
C_LABEL     = colors.HexColor("#4a5568")
C_BLANC_BLU = colors.HexColor("#a8d8ff")


def _fmt_date(d):
    try:
        p = d.split("-")
        return f"{p[2]}/{p[1]}/{p[0]}"
    except Exception:
        return d or "—"


def _fmt_montant(m):
    """Format int with space as thousands separator: 15000 → '15 000'."""
    s = str(int(m))
    result = ""
    for i, ch in enumerate(reversed(s)):
        if i > 0 and i % 3 == 0:
            result = " " + result
        result = ch + result
    return result


def _recuperer_donnees_recu(abonnement_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT r.numero_recu, r.date_emission, r.montant, r.duree_jours, "
            "       a.date_debut, a.date_fin, "
            "       l.nom, l.prenom, l.telephone, "
            "       t.nom AS type_nom "
            "FROM Recus r "
            "JOIN Abonnements a ON a.id = r.abonnement_id "
            "JOIN Lecteurs l ON l.id = a.lecteur_id "
            "JOIN TypesAbonnement t ON t.id = a.type_abonnement_id "
            "WHERE r.abonnement_id = ?",
            (abonnement_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise ValueError(f"Aucun reçu trouvé pour l'abonnement {abonnement_id}")
    return dict(row)


def generer_recu_pdf(abonnement_id):
    """Construit le PDF du reçu redesigné et enregistre son chemin en base."""
    donnees = _recuperer_donnees_recu(abonnement_id)
    os.makedirs(DOSSIER_RECUS, exist_ok=True)

    nom_bib = get_parametre("nom_bibliotheque", "Bibliothèque")
    devise  = get_parametre("devise", "FCFA")

    chemin_pdf = os.path.join(DOSSIER_RECUS, f"{donnees['numero_recu']}.pdf")

    PAGE_W, PAGE_H = A4
    MARGIN  = 2 * cm
    AVAIL_W = PAGE_W - 2 * MARGIN

    doc = SimpleDocTemplate(
        chemin_pdf, pagesize=A4,
        topMargin=MARGIN, bottomMargin=2 * cm,
        leftMargin=MARGIN, rightMargin=MARGIN,
    )

    nom_complet = f"{donnees['nom']} {donnees.get('prenom') or ''}".strip()
    montant_str = f"{_fmt_montant(donnees['montant'])} {devise}"

    # ─── Styles ───────────────────────────────────────────
    s_bib    = ParagraphStyle("bib", fontName="Helvetica-Bold",
                              fontSize=18, textColor=colors.white, leading=22)
    s_bib_s  = ParagraphStyle("bibs", fontName="Helvetica",
                              fontSize=9, textColor=C_BLANC_BLU)
    s_r_lbl  = ParagraphStyle("rlbl", fontName="Helvetica-Bold",
                              fontSize=12, textColor=colors.white,
                              alignment=TA_RIGHT)
    s_r_val  = ParagraphStyle("rval", fontName="Helvetica",
                              fontSize=9, textColor=C_BLANC_BLU,
                              alignment=TA_RIGHT)
    s_sec    = ParagraphStyle("sec",  fontName="Helvetica-Bold",
                              fontSize=10, textColor=C_BLEU,
                              spaceBefore=10, spaceAfter=6)
    s_lbl    = ParagraphStyle("lbl",  fontName="Helvetica-Bold",
                              fontSize=10, textColor=C_LABEL)
    s_val    = ParagraphStyle("val",  fontName="Helvetica",
                              fontSize=10, textColor=C_TEXTE)
    s_mnt_l  = ParagraphStyle("mntl", fontName="Helvetica",
                              fontSize=10, textColor=C_VERT,
                              alignment=TA_CENTER)
    s_mnt_v  = ParagraphStyle("mntv", fontName="Helvetica-Bold",
                              fontSize=24, textColor=colors.white,
                              alignment=TA_CENTER)
    s_paye   = ParagraphStyle("paye", fontName="Helvetica-Bold",
                              fontSize=10, textColor=C_VERT,
                              alignment=TA_CENTER)
    s_foot   = ParagraphStyle("foot", fontName="Helvetica",
                              fontSize=8.5, textColor=colors.grey,
                              alignment=TA_CENTER)

    ts_base = TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])

    elements = []

    # ═══════════════════════════════════════════════════════
    # HEADER : fond bleu — nom bibliothèque à gauche,
    #          numéro de reçu + date à droite
    # ═══════════════════════════════════════════════════════
    h_left  = [Paragraph(nom_bib, s_bib), Paragraph("Gestion des abonnements", s_bib_s)]
    h_right = [
        Paragraph("REÇU D'ABONNEMENT", s_r_lbl),
        Paragraph(f"N° {donnees['numero_recu']}", s_r_val),
        Paragraph(f"Date : {_fmt_date(donnees['date_emission'])}", s_r_val),
    ]
    t_header = Table(
        [[h_left, h_right]],
        colWidths=[AVAIL_W * 0.58, AVAIL_W * 0.42],
    )
    t_header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_BLEU),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING",   (0, 0), (0,  -1), 18),
        ("RIGHTPADDING",  (1, 0), (1,  -1), 18),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t_header)

    # Bande verte
    t_vert = Table([[""]], colWidths=[AVAIL_W], rowHeights=[4])
    t_vert.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_VERT),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_vert)
    elements.append(Spacer(1, 0.6 * cm))

    # ═══════════════════════════════════════════════════════
    # BLOC MEMBRE
    # ═══════════════════════════════════════════════════════
    elements.append(Paragraph("INFORMATIONS DU MEMBRE", s_sec))

    m_data = [
        [Paragraph("Nom complet", s_lbl),  Paragraph(nom_complet, s_val)],
        [Paragraph("Téléphone",   s_lbl),  Paragraph(donnees.get("telephone") or "—", s_val)],
    ]
    t_m = Table(m_data, colWidths=[4.5 * cm, AVAIL_W - 4.5 * cm])
    t_m.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), C_BLEU_L),
        ("LINEBELOW",   (0, 0), (-1, -2), 0.5, C_BLEU_BD),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("BOX",         (0, 0), (-1, -1), 0.5, C_BLEU_BD),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t_m)
    elements.append(Spacer(1, 0.5 * cm))

    # ═══════════════════════════════════════════════════════
    # BLOC ABONNEMENT
    # ═══════════════════════════════════════════════════════
    elements.append(Paragraph("DÉTAILS DE L'ABONNEMENT", s_sec))

    a_data = [
        [Paragraph("Formule",       s_lbl),
         Paragraph(f"{donnees['type_nom']} ({donnees['duree_jours']} jours)", s_val)],
        [Paragraph("Date de début", s_lbl),
         Paragraph(_fmt_date(donnees["date_debut"]), s_val)],
        [Paragraph("Date de fin",   s_lbl),
         Paragraph(_fmt_date(donnees["date_fin"]), s_val)],
    ]
    t_a = Table(a_data, colWidths=[4.5 * cm, AVAIL_W - 4.5 * cm])
    t_a.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_GRIS_L),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, C_GRIS_BD),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_GRIS_BD),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t_a)
    elements.append(Spacer(1, 0.7 * cm))

    # ═══════════════════════════════════════════════════════
    # MONTANT
    # ═══════════════════════════════════════════════════════
    t_mnt = Table(
        [
            [Paragraph("MONTANT ENCAISSÉ", s_mnt_l)],
            [Paragraph(montant_str,         s_mnt_v)],
            [Paragraph("PAYÉ",              s_paye)],
        ],
        colWidths=[AVAIL_W],
    )
    t_mnt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_BLEU),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t_mnt)
    elements.append(Spacer(1, 1 * cm))

    # ═══════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════
    elements.append(HRFlowable(width=AVAIL_W, color=C_GRIS_BD, thickness=0.5))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Merci de votre confiance et fidélité.", s_foot))
    elements.append(Paragraph(
        f"{nom_bib}  ·  tonde410@gmail.com  ·  +226 74 64 13 06",
        s_foot,
    ))

    doc.build(elements)

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE Recus SET chemin_pdf = ? WHERE abonnement_id = ?",
            (chemin_pdf, abonnement_id),
        )
        conn.commit()
    finally:
        conn.close()

    return chemin_pdf
