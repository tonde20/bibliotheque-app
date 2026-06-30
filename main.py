"""
main.py — Interface graphique principale de la bibliothèque.
Lancer avec : python main.py
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QComboBox, QDialog, QFormLayout,
    QDialogButtonBox, QHeaderView, QFrame, QSpinBox, QStatusBar,
    QSizePolicy, QDateEdit, QFileDialog,
)
from PySide6.QtCore import Qt, QDate, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor, QIcon

from app import livres, lecteurs, abonnements, emprunts
from app.abonnements import actualiser_statuts_abonnements
from app import tresorerie
from app.migrations import appliquer_migrations
from app.licence import (verifier_licence, installer_licence,
                         jours_restants, LicenceAbsente, LicenceInvalide, LicenceExpiree)


# ─────────────────────────────────────────────
#  Feuille de style globale
# ─────────────────────────────────────────────

QSS = """
QMainWindow, QDialog {
    background-color: #f0f4f8;
}

QTabWidget::pane {
    border: none;
    background-color: #f0f4f8;
}

QTabBar::tab {
    background: #dce6f0;
    color: #4a5568;
    padding: 10px 22px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: #2b6cb0;
    color: white;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background: #bee3f8;
    color: #2b6cb0;
}

QTableWidget {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #edf2f7;
    font-size: 13px;
    selection-background-color: #ebf8ff;
    selection-color: #2b6cb0;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
}

QHeaderView::section {
    background-color: #2b6cb0;
    color: white;
    padding: 8px 10px;
    border: none;
    font-size: 12px;
    font-weight: 600;
}

QHeaderView::section:first {
    border-top-left-radius: 6px;
}

QHeaderView::section:last {
    border-top-right-radius: 6px;
}

QLineEdit {
    background: white;
    border: 1.5px solid #cbd5e0;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    color: #2d3748;
}

QLineEdit:focus {
    border-color: #3182ce;
}

QComboBox {
    background: white;
    border: 1.5px solid #cbd5e0;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    color: #2d3748;
    min-width: 180px;
}

QComboBox:focus {
    border-color: #3182ce;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QSpinBox {
    background: white;
    border: 1.5px solid #cbd5e0;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: #2d3748;
}

QSpinBox:focus {
    border-color: #3182ce;
}

QPushButton {
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton:hover {
    opacity: 0.9;
}

QLabel {
    color: #2d3748;
    font-size: 13px;
}

QFormLayout QLabel {
    font-weight: 600;
    color: #4a5568;
}

QMessageBox {
    background-color: #f0f4f8;
    font-size: 13px;
}

QStatusBar {
    background: #2b6cb0;
    color: white;
    font-size: 12px;
    padding: 2px 8px;
}

QFrame[frameShape="4"] {
    color: #e2e8f0;
}
"""


# ─────────────────────────────────────────────
#  Helpers UI
# ─────────────────────────────────────────────

def _table(colonnes):
    t = QTableWidget()
    t.setColumnCount(len(colonnes))
    t.setHorizontalHeaderLabels(colonnes)
    t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setStyleSheet("QTableWidget { alternate-background-color: #f7fafc; }")
    t.setShowGrid(False)
    return t


def _item(texte, rouge=False, gras=False):
    it = QTableWidgetItem(str(texte) if texte is not None else "—")
    it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    if rouge:
        it.setForeground(QColor("#c53030"))
        it.setBackground(QColor("#fff5f5"))
    if gras:
        f = it.font(); f.setBold(True); it.setFont(f)
    return it


def _btn(texte, bg="#2b6cb0", fg="white"):
    b = QPushButton(texte)
    b.setStyleSheet(
        f"QPushButton {{ background-color:{bg}; color:{fg}; }}"
        f"QPushButton:hover {{ background-color:{_darken(bg)}; }}"
        f"QPushButton:pressed {{ background-color:{_darken(bg, 20)}; }}"
    )
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _darken(hex_color, amount=15):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = max(0, r - amount), max(0, g - amount), max(0, b - amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def _titre_section(texte):
    l = QLabel(texte)
    l.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    l.setStyleSheet("color: #2b6cb0; margin-bottom: 4px;")
    return l


def _carte(widget):
    """Enveloppe un widget dans une carte blanche avec ombre légère."""
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame { background: white; border-radius: 10px; "
        "border: 1px solid #e2e8f0; }"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 12, 12, 12)
    lay.addWidget(widget)
    return frame


# ─────────────────────────────────────────────
#  Onglet Livres
# ─────────────────────────────────────────────

class OngletLivres(QWidget):
    COLS = ["ID", "Titre", "Auteur", "ISBN", "Catégorie", "Dispo", "Total", "Statut", "Date ajout"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(_titre_section("Catalogue des livres"))

        barre = QHBoxLayout()
        self.champ_recherche = QLineEdit()
        self.champ_recherche.setPlaceholderText("  Rechercher par titre, auteur ou ISBN…")
        self.champ_recherche.returnPressed.connect(self.rechercher)
        barre.addWidget(self.champ_recherche)
        btn_rech = _btn("Rechercher", "#718096")
        btn_rech.clicked.connect(self.rechercher)
        barre.addWidget(btn_rech)
        barre.addSpacing(8)
        btn_tout = _btn("Tout afficher", "#4a5568")
        btn_tout.clicked.connect(lambda: (self.champ_recherche.clear(), self.charger()))
        barre.addWidget(btn_tout)
        barre.addStretch()
        btn_ajouter = _btn("+ Ajouter un livre", "#276749")
        btn_ajouter.clicked.connect(self.ajouter)
        barre.addWidget(btn_ajouter)
        btn_modifier = _btn("Modifier", "#2b6cb0")
        btn_modifier.clicked.connect(self.modifier)
        barre.addWidget(btn_modifier)
        btn_supprimer = _btn("Supprimer", "#c53030")
        btn_supprimer.clicked.connect(self.supprimer)
        barre.addWidget(btn_supprimer)
        layout.addLayout(barre)

        self.table = _table(self.COLS)
        layout.addWidget(self.table)

        self.label_nb = QLabel()
        self.label_nb.setStyleSheet("color: #718096; font-size: 12px;")
        layout.addWidget(self.label_nb)

        self.charger()

    def charger(self, liste=None):
        donnees = liste if liste is not None else livres.lister_livres()
        self.table.setRowCount(len(donnees))
        for i, l in enumerate(donnees):
            epuise = l.get("quantite_disponible", 1) <= 0
            self.table.setItem(i, 0, _item(l.get("id")))
            self.table.setItem(i, 1, _item(l.get("titre"), gras=True))
            self.table.setItem(i, 2, _item(l.get("auteur")))
            self.table.setItem(i, 3, _item(l.get("isbn")))
            self.table.setItem(i, 4, _item(l.get("categorie")))
            self.table.setItem(i, 5, _item(l.get("quantite_disponible"), rouge=epuise, gras=True))
            self.table.setItem(i, 6, _item(l.get("quantite_total")))
            self.table.setItem(i, 7, _item(l.get("statut"), rouge=epuise))
            self.table.setItem(i, 8, _item(l.get("date_ajout")))
        self.label_nb.setText(f"{len(donnees)} livre(s) affiché(s)")

    def rechercher(self):
        mot = self.champ_recherche.text().strip()
        self.charger(livres.rechercher_livre(mot) if mot else None)

    def ajouter(self):
        dlg = DialogueLivre(self)
        if dlg.exec():
            livres.ajouter_livre(**dlg.valeurs())
            self.charger()

    def modifier(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection requise", "Sélectionnez un livre à modifier.")
            return
        livre_id = int(self.table.item(row, 0).text())
        donnees = {
            "titre": self.table.item(row, 1).text(),
            "auteur": self.table.item(row, 2).text(),
            "isbn": self.table.item(row, 3).text(),
            "categorie": self.table.item(row, 4).text(),
            "quantite_disponible": int(self.table.item(row, 5).text()),
            "quantite_total": int(self.table.item(row, 6).text()),
        }
        dlg = DialogueModifierLivre(donnees, self)
        if dlg.exec():
            vals = dlg.valeurs()
            anciennes_sorties = donnees["quantite_total"] - donnees["quantite_disponible"]
            nouvelle_dispo = max(0, vals["quantite_total"] - anciennes_sorties)
            livres.modifier_livre(
                livre_id,
                titre=vals["titre"],
                auteur=vals["auteur"] or None,
                isbn=vals["isbn"] or None,
                categorie=vals["categorie"] or None,
                quantite_total=vals["quantite_total"],
                quantite_disponible=nouvelle_dispo,
            )
            self.charger()

    def supprimer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection requise", "Sélectionnez un livre à supprimer.")
            return
        livre_id = int(self.table.item(row, 0).text())
        titre = self.table.item(row, 1).text()
        dispo = int(self.table.item(row, 5).text())
        total = int(self.table.item(row, 6).text())
        if dispo < total:
            QMessageBox.warning(self, "Impossible",
                f"« {titre} » a encore {total - dispo} exemplaire(s) sorti(s).\n"
                "Attendez le retour avant de supprimer.")
            return
        rep = QMessageBox.question(self, "Confirmer la suppression",
            f"Supprimer définitivement « {titre} » ({total} exemplaire(s)) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            livres.supprimer_livre(livre_id)
            self.charger()


class DialogueLivre(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un livre")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #f0f4f8;")
        layout = QVBoxLayout(self)
        layout.addWidget(_titre_section("Nouveau livre"))
        form = QFormLayout()
        form.setSpacing(10)
        self.titre = QLineEdit(); form.addRow("Titre *", self.titre)
        self.auteur = QLineEdit(); form.addRow("Auteur", self.auteur)
        self.isbn = QLineEdit(); form.addRow("ISBN", self.isbn)
        self.categorie = QLineEdit(); form.addRow("Catégorie", self.categorie)
        self.quantite = QSpinBox()
        self.quantite.setRange(1, 999)
        self.quantite.setValue(1)
        self.quantite.setSuffix(" exemplaire(s)")
        form.addRow("Quantité", self.quantite)
        layout.addLayout(form)
        layout.addSpacing(8)
        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Enregistrer")
        boutons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("background:#276749;color:white;padding:7px 20px;border-radius:6px;font-weight:bold;")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#718096;color:white;padding:7px 20px;border-radius:6px;")
        boutons.accepted.connect(self._valider)
        boutons.rejected.connect(self.reject)
        layout.addWidget(boutons)

    def _valider(self):
        if not self.titre.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le titre est obligatoire.")
            return
        self.accept()

    def valeurs(self):
        return {
            "titre": self.titre.text().strip(),
            "auteur": self.auteur.text().strip() or None,
            "isbn": self.isbn.text().strip() or None,
            "categorie": self.categorie.text().strip() or None,
            "quantite": self.quantite.value(),
        }


class DialogueModifierLivre(QDialog):
    def __init__(self, donnees, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier un livre")
        self.setMinimumWidth(420)
        self.setStyleSheet("background-color: #f0f4f8;")
        layout = QVBoxLayout(self)
        layout.addWidget(_titre_section("Modifier le livre"))

        sorties = donnees["quantite_total"] - donnees["quantite_disponible"]
        if sorties > 0:
            info = QLabel(f"⚠  {sorties} exemplaire(s) actuellement sorti(s) — la quantité totale ne peut pas descendre en dessous de {sorties}.")
            info.setStyleSheet("color: #c05621; background: #fffaf0; border-radius:6px; padding:6px;")
            info.setWordWrap(True)
            layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)
        self.titre = QLineEdit(donnees["titre"]); form.addRow("Titre *", self.titre)
        self.auteur = QLineEdit(donnees["auteur"] if donnees["auteur"] != "—" else ""); form.addRow("Auteur", self.auteur)
        self.isbn = QLineEdit(donnees["isbn"] if donnees["isbn"] != "—" else ""); form.addRow("ISBN", self.isbn)
        self.categorie = QLineEdit(donnees["categorie"] if donnees["categorie"] != "—" else ""); form.addRow("Catégorie", self.categorie)

        self._sorties = sorties
        self.quantite = QSpinBox()
        self.quantite.setRange(max(1, sorties), 999)
        self.quantite.setValue(donnees["quantite_total"])
        self.quantite.setSuffix(" exemplaire(s) au total")
        form.addRow("Quantité totale", self.quantite)

        layout.addLayout(form)
        layout.addSpacing(8)
        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Enregistrer")
        boutons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("background:#2b6cb0;color:white;padding:7px 20px;border-radius:6px;font-weight:bold;")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#718096;color:white;padding:7px 20px;border-radius:6px;")
        boutons.accepted.connect(self._valider)
        boutons.rejected.connect(self.reject)
        layout.addWidget(boutons)

    def _valider(self):
        if not self.titre.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le titre est obligatoire.")
            return
        self.accept()

    def valeurs(self):
        return {
            "titre": self.titre.text().strip(),
            "auteur": self.auteur.text().strip(),
            "isbn": self.isbn.text().strip(),
            "categorie": self.categorie.text().strip(),
            "quantite_total": self.quantite.value(),
        }


# ─────────────────────────────────────────────
#  Onglet Lecteurs & Abonnements
# ─────────────────────────────────────────────

class OngletLecteurs(QWidget):
    COLS = ["ID", "Nom", "Prénom", "Téléphone", "Email", "Date d'inscription"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(_titre_section("Lecteurs & Abonnements"))

        barre = QHBoxLayout()
        self.champ_recherche = QLineEdit()
        self.champ_recherche.setPlaceholderText("  Rechercher un lecteur…")
        self.champ_recherche.returnPressed.connect(self.rechercher)
        barre.addWidget(self.champ_recherche)
        btn_rech = _btn("Rechercher", "#718096")
        btn_rech.clicked.connect(self.rechercher)
        barre.addWidget(btn_rech)
        btn_tout = _btn("Tout afficher", "#4a5568")
        btn_tout.clicked.connect(lambda: (self.champ_recherche.clear(), self.charger()))
        barre.addWidget(btn_tout)
        barre.addStretch()
        btn_ajouter = _btn("+ Nouveau lecteur", "#276749")
        btn_ajouter.clicked.connect(self.ajouter_lecteur)
        barre.addWidget(btn_ajouter)
        btn_suppr = _btn("Supprimer", "#c53030")
        btn_suppr.clicked.connect(self.supprimer_lecteur)
        barre.addWidget(btn_suppr)
        layout.addLayout(barre)

        self.table = _table(self.COLS)
        self.table.selectionModel().selectionChanged.connect(self._on_selection)
        layout.addWidget(self.table)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(sep)

        panneau = QHBoxLayout()
        self.label_selection = QLabel("Sélectionnez un lecteur pour gérer son abonnement.")
        self.label_selection.setStyleSheet("color: #718096; font-style: italic;")
        panneau.addWidget(self.label_selection)
        panneau.addStretch()
        self.btn_annuler_abo = _btn("Annuler l'abonnement sélectionné", "#c53030")
        self.btn_annuler_abo.clicked.connect(self.annuler_abonnement)
        self.btn_annuler_abo.setEnabled(False)
        panneau.addWidget(self.btn_annuler_abo)
        self.btn_abo = _btn("Créer un abonnement", "#6b46c1")
        self.btn_abo.clicked.connect(self.creer_abonnement)
        self.btn_abo.setEnabled(False)
        panneau.addWidget(self.btn_abo)
        layout.addLayout(panneau)

        # Tableau abonnements du lecteur sélectionné
        layout.addWidget(QLabel("Abonnements du lecteur sélectionné :"))
        self.table_abo = _table(["ID", "Formule", "Début", "Fin", "Montant", "Statut"])
        self.table_abo.setMaximumHeight(160)
        layout.addWidget(self.table_abo)

        self._lecteur_id = None
        self.charger()

    def charger(self, liste=None):
        donnees = liste if liste is not None else lecteurs.lister_lecteurs()
        self.table.setRowCount(len(donnees))
        for i, lec in enumerate(donnees):
            for j, champ in enumerate(["id", "nom", "prenom", "telephone", "email", "date_inscription"]):
                self.table.setItem(i, j, _item(lec.get(champ), gras=(champ == "nom")))

    def rechercher(self):
        mot = self.champ_recherche.text().strip()
        self.charger(lecteurs.rechercher_lecteur(mot) if mot else None)

    def _on_selection(self):
        row = self.table.currentRow()
        if row < 0:
            self._lecteur_id = None
            self.label_selection.setText("Sélectionnez un lecteur pour gérer son abonnement.")
            self.label_selection.setStyleSheet("color: #718096; font-style: italic;")
            self.btn_abo.setEnabled(False)
            self.btn_annuler_abo.setEnabled(False)
            self.table_abo.setRowCount(0)
            return
        self._lecteur_id = int(self.table.item(row, 0).text())
        nom = self.table.item(row, 1).text()
        prenom = self.table.item(row, 2).text()
        self.label_selection.setText(f"Lecteur sélectionné : {nom} {prenom}")
        self.label_selection.setStyleSheet("color: #2b6cb0; font-weight: bold; font-style: normal;")
        self.btn_abo.setEnabled(True)
        self._charger_abonnements()

    def _charger_abonnements(self):
        if not self._lecteur_id:
            return
        rows = abonnements.lister_abonnements_lecteur(self._lecteur_id)
        self.table_abo.setRowCount(len(rows))
        for i, a in enumerate(rows):
            annule = a["statut"] == "annule"
            expire = a["statut"] == "expire"
            rouge = annule or expire
            self.table_abo.setItem(i, 0, _item(a["id"]))
            self.table_abo.setItem(i, 1, _item(a["type_nom"], gras=True))
            self.table_abo.setItem(i, 2, _item(a["date_debut"]))
            self.table_abo.setItem(i, 3, _item(a["date_fin"]))
            self.table_abo.setItem(i, 4, _item(f"{a['montant_paye']:.0f} FCFA"))
            self.table_abo.setItem(i, 5, _item(a["statut"], rouge=rouge))
        self.btn_annuler_abo.setEnabled(len(rows) > 0)

    def ajouter_lecteur(self):
        dlg = DialogueLecteur(self)
        if dlg.exec():
            lecteurs.ajouter_lecteur(**dlg.valeurs())
            self.charger()

    def supprimer_lecteur(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection requise", "Sélectionnez un lecteur à supprimer.")
            return
        lecteur_id = int(self.table.item(row, 0).text())
        nom = self.table.item(row, 1).text()
        prenom = self.table.item(row, 2).text()
        rep = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer « {nom} {prenom} » et toutes ses données (abonnements, emprunts, trésorerie) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            lecteurs.supprimer_lecteur(lecteur_id)
            self.table_abo.setRowCount(0)
            self._lecteur_id = None
            self.btn_abo.setEnabled(False)
            self.btn_annuler_abo.setEnabled(False)
            self.label_selection.setText("Sélectionnez un lecteur pour gérer son abonnement.")
            self.label_selection.setStyleSheet("color: #718096; font-style: italic;")
            self.charger()

    def annuler_abonnement(self):
        row = self.table_abo.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection", "Sélectionnez un abonnement dans le tableau du bas.")
            return
        abo_id = int(self.table_abo.item(row, 0).text())
        statut = self.table_abo.item(row, 5).text()
        if statut != "actif":
            QMessageBox.warning(self, "Impossible", f"Cet abonnement est déjà « {statut} ».")
            return
        formule = self.table_abo.item(row, 1).text()
        rep = QMessageBox.question(self, "Confirmer l'annulation",
            f"Annuler l'abonnement « {formule} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            abonnements.annuler_abonnement(abo_id)
            self._charger_abonnements()

    def creer_abonnement(self):
        if not self._lecteur_id:
            return
        types = abonnements.lister_types_abonnement()
        dlg = DialogueAbonnement(types, self)
        if dlg.exec():
            type_id, montant, duree_override = dlg.valeurs()
            try:
                res = abonnements.creer_abonnement(
                    self._lecteur_id, type_id,
                    montant_paye=montant,
                    duree_jours_override=duree_override,
                )
                pdf   = res.get("chemin_pdf", "")
                carte = res.get("chemin_carte", "")
                msg = (
                    f"Abonnement créé avec succès !\n\n"
                    f"N° reçu : {res['numero_recu']}\n"
                    f"Du {res['date_debut']} au {res['date_fin']}\n"
                    f"Durée : {res['duree_jours']} jours\n"
                    f"Montant : {res['montant']:.0f} FCFA"
                )
                QMessageBox.information(self, "Abonnement enregistré", msg)
                # Ouvrir automatiquement le reçu et la carte dans le lecteur PDF
                import os as _os
                if pdf and _os.path.isfile(pdf):
                    _os.startfile(pdf)
                if carte and _os.path.isfile(carte):
                    _os.startfile(carte)
                self._charger_abonnements()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class DialogueLecteur(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau lecteur")
        self.setMinimumWidth(460)
        self.setStyleSheet("background-color: #f0f4f8;")
        layout = QVBoxLayout(self)
        layout.addWidget(_titre_section("Nouveau lecteur"))
        form = QFormLayout()
        form.setSpacing(10)
        self.nom = QLineEdit(); form.addRow("Nom *", self.nom)
        self.prenom = QLineEdit(); form.addRow("Prénom", self.prenom)
        self.telephone = QLineEdit(); form.addRow("Téléphone", self.telephone)
        self.email = QLineEdit(); form.addRow("Email", self.email)
        self.adresse = QLineEdit(); form.addRow("Adresse", self.adresse)

        # Champ photo
        photo_layout = QHBoxLayout()
        self.photo = QLineEdit()
        self.photo.setPlaceholderText("Chemin vers une photo (optionnel)…")
        self.photo.setReadOnly(True)
        photo_layout.addWidget(self.photo)
        btn_photo = _btn("Parcourir…", "#4a5568")
        btn_photo.setFixedWidth(90)
        btn_photo.clicked.connect(self._choisir_photo)
        photo_layout.addWidget(btn_photo)
        form.addRow("Photo", photo_layout)

        layout.addLayout(form)
        layout.addSpacing(8)
        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Enregistrer")
        boutons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("background:#276749;color:white;padding:7px 20px;border-radius:6px;font-weight:bold;")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#718096;color:white;padding:7px 20px;border-radius:6px;")
        boutons.accepted.connect(self._valider)
        boutons.rejected.connect(self.reject)
        layout.addWidget(boutons)

    def _choisir_photo(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner une photo", "",
            "Images (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        if chemin:
            self.photo.setText(chemin)

    def _valider(self):
        if not self.nom.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire.")
            return
        self.accept()

    def valeurs(self):
        return {
            "nom": self.nom.text().strip(),
            "prenom": self.prenom.text().strip() or None,
            "telephone": self.telephone.text().strip() or None,
            "email": self.email.text().strip() or None,
            "adresse": self.adresse.text().strip() or None,
            "photo": self.photo.text().strip() or None,
        }


class DialogueAbonnement(QDialog):
    PERSONNALISE = "__personnalise__"

    def __init__(self, types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Créer un abonnement")
        self.setMinimumWidth(420)
        self.setStyleSheet("background-color: #f0f4f8;")
        self._types = types

        layout = QVBoxLayout(self)
        layout.addWidget(_titre_section("Nouvel abonnement"))

        form = QFormLayout()
        form.setSpacing(12)

        self.combo = QComboBox()
        for t in sorted(types, key=lambda x: x["duree_jours"]):
            label = f"{t['nom']}  —  {t['prix']:.0f} FCFA  ({t['duree_jours']} j)"
            self.combo.addItem(label, t["id"])
        self.combo.addItem("Personnalisé (nombre de jours libre)", self.PERSONNALISE)
        self.combo.currentIndexChanged.connect(self._maj_champs)
        form.addRow("Formule", self.combo)

        self.spin_duree = QSpinBox()
        self.spin_duree.setRange(1, 3650)
        self.spin_duree.setValue(30)
        self.spin_duree.setSuffix(" jours")
        self.label_duree = QLabel("Durée personnalisée")
        form.addRow(self.label_duree, self.spin_duree)
        self.spin_duree.setVisible(False)
        self.label_duree.setVisible(False)

        self.montant = QSpinBox()
        self.montant.setRange(0, 9999999)
        self.montant.setSuffix(" FCFA")
        form.addRow("Montant payé", self.montant)

        layout.addLayout(form)
        layout.addSpacing(10)

        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Valider l'abonnement")
        boutons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("background:#6b46c1;color:white;padding:7px 20px;border-radius:6px;font-weight:bold;")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#718096;color:white;padding:7px 20px;border-radius:6px;")
        boutons.accepted.connect(self.accept)
        boutons.rejected.connect(self.reject)
        layout.addWidget(boutons)

        self._maj_champs()

    def _maj_champs(self):
        data = self.combo.currentData()
        est_perso = (data == self.PERSONNALISE)
        self.spin_duree.setVisible(est_perso)
        self.label_duree.setVisible(est_perso)
        if not est_perso:
            idx = self.combo.currentIndex()
            # Trouver le type correspondant
            type_id = data
            for t in self._types:
                if t["id"] == type_id:
                    self.montant.setValue(int(t["prix"]))
                    break

    def valeurs(self):
        """Retourne (type_id, montant, duree_override_ou_None)."""
        data = self.combo.currentData()
        montant = self.montant.value()
        if data == self.PERSONNALISE:
            # Utiliser le premier type comme base (peu importe, la durée sera surchargée)
            type_id = self._types[0]["id"]
            return type_id, montant, self.spin_duree.value()
        return data, montant, None


# ─────────────────────────────────────────────
#  Onglet Emprunts
# ─────────────────────────────────────────────

class OngletEmprunts(QWidget):
    COLS = ["ID", "Livre", "Lecteur", "Date sortie", "Retour prévu", "Retard (j)", "En retard"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(_titre_section("Gestion des emprunts"))

        barre = QHBoxLayout()
        btn_sortie = _btn("Sortir un livre", "#c05621")
        btn_sortie.clicked.connect(self.sortir_livre)
        barre.addWidget(btn_sortie)
        barre.addSpacing(8)
        btn_retour = _btn("Enregistrer un retour", "#276749")
        btn_retour.clicked.connect(self.retourner_livre)
        barre.addWidget(btn_retour)
        barre.addStretch()
        btn_refresh = _btn("Actualiser", "#4a5568")
        btn_refresh.clicked.connect(self.charger)
        barre.addWidget(btn_refresh)
        layout.addLayout(barre)

        self.table = _table(self.COLS)
        layout.addWidget(self.table)

        self.label_nb = QLabel()
        self.label_nb.setStyleSheet("color: #718096; font-size: 12px;")
        layout.addWidget(self.label_nb)

        self.charger()

    def charger(self):
        donnees = emprunts.lister_emprunts_en_cours()
        self.table.setRowCount(len(donnees))
        nb_retard = 0
        for i, e in enumerate(donnees):
            en_retard = e["en_retard"]
            if en_retard:
                nb_retard += 1
            self.table.setItem(i, 0, _item(e["id"]))
            self.table.setItem(i, 1, _item(e["livre_titre"], gras=True))
            nom = f"{e['lecteur_nom']} {e.get('lecteur_prenom') or ''}".strip()
            self.table.setItem(i, 2, _item(nom))
            self.table.setItem(i, 3, _item(e["date_sortie"]))
            self.table.setItem(i, 4, _item(e["date_retour_prevue"]))
            self.table.setItem(i, 5, _item(e["jours_retard_actuel"], rouge=en_retard))
            self.table.setItem(i, 6, _item("Oui" if en_retard else "Non", rouge=en_retard))
        total = len(donnees)
        self.label_nb.setText(f"{total} emprunt(s) en cours  —  {nb_retard} en retard")

    def sortir_livre(self):
        livres_dispo = livres.lister_livres(statut="disponible")
        lecs = lecteurs.lister_lecteurs()
        if not livres_dispo:
            QMessageBox.information(self, "Aucun livre", "Aucun livre disponible en ce moment.")
            return
        if not lecs:
            QMessageBox.information(self, "Aucun lecteur", "Aucun lecteur enregistré.")
            return
        dlg = DialogueSortie(livres_dispo, lecs, self)
        if dlg.exec():
            livre_id, lecteur_id, duree, date_sortie = dlg.valeurs()
            try:
                res = emprunts.sortir_livre(livre_id, lecteur_id, duree_jours=duree, date_sortie=date_sortie)
                QMessageBox.information(
                    self, "Sortie enregistrée",
                    f"Livre sorti avec succès.\nRetour prévu le : {res['date_retour_prevue']}"
                )
                self.charger()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def retourner_livre(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection requise", "Sélectionnez un emprunt dans la liste.")
            return
        emprunt_id = int(self.table.item(row, 0).text())
        livre_titre = self.table.item(row, 1).text()
        rep = QMessageBox.question(
            self, "Confirmer le retour",
            f"Enregistrer le retour de « {livre_titre} » aujourd'hui ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                res = emprunts.retourner_livre(emprunt_id)
                if res["jours_retard"] > 0:
                    msg = (
                        f"Retour enregistré avec retard.\n\n"
                        f"Retard : {res['jours_retard']} jour(s)\n"
                        f"Pénalité : {res['penalite']:.0f} FCFA"
                    )
                else:
                    msg = "Retour enregistré dans les délais. Merci !"
                QMessageBox.information(self, "Retour enregistré", msg)
                self.charger()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class DialogueSortie(QDialog):
    def __init__(self, livres_dispo, lecs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sortir un livre")
        self.setMinimumWidth(440)
        self.setStyleSheet("background-color: #f0f4f8;")

        layout = QVBoxLayout(self)
        layout.addWidget(_titre_section("Nouvelle sortie"))

        form = QFormLayout()
        form.setSpacing(12)

        self.combo_livre = QComboBox()
        for l in livres_dispo:
            self.combo_livre.addItem(f"{l['titre']}  ({l['auteur'] or '—'})", l["id"])
        form.addRow("Livre", self.combo_livre)

        self.combo_lecteur = QComboBox()
        for lec in lecs:
            nom = f"{lec['nom']} {lec.get('prenom') or ''}".strip()
            self.combo_lecteur.addItem(nom, lec["id"])
        form.addRow("Lecteur", self.combo_lecteur)

        self.date_sortie = QDateEdit()
        self.date_sortie.setCalendarPopup(True)
        self.date_sortie.setDate(QDate.currentDate())
        self.date_sortie.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date de sortie", self.date_sortie)

        self.duree = QSpinBox()
        self.duree.setRange(1, 365)
        self.duree.setValue(14)
        self.duree.setSuffix(" jours")
        form.addRow("Durée du prêt", self.duree)

        layout.addLayout(form)
        layout.addSpacing(10)

        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        boutons.button(QDialogButtonBox.StandardButton.Ok).setText("Enregistrer la sortie")
        boutons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("background:#c05621;color:white;padding:7px 20px;border-radius:6px;font-weight:bold;")
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#718096;color:white;padding:7px 20px;border-radius:6px;")
        boutons.accepted.connect(self.accept)
        boutons.rejected.connect(self.reject)
        layout.addWidget(boutons)

    def valeurs(self):
        d = self.date_sortie.date()
        date_iso = f"{d.year()}-{d.month():02d}-{d.day():02d}"
        return self.combo_livre.currentData(), self.combo_lecteur.currentData(), self.duree.value(), date_iso


# ─────────────────────────────────────────────
#  Onglet Retards
# ─────────────────────────────────────────────

class OngletRetards(QWidget):
    COLS = ["ID", "Livre", "Lecteur", "Téléphone", "Retour prévu", "Retard (j)", "Pénalité (FCFA)"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(_titre_section("Emprunts en retard"))

        barre = QHBoxLayout()
        self.label_total = QLabel()
        self.label_total.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.label_total.setStyleSheet("color: #c53030;")
        barre.addWidget(self.label_total)
        barre.addStretch()
        btn_refresh = _btn("Actualiser", "#4a5568")
        btn_refresh.clicked.connect(self.charger)
        barre.addWidget(btn_refresh)
        layout.addLayout(barre)

        self.table = _table(self.COLS)
        layout.addWidget(self.table)

        self.charger()

    def charger(self):
        from app.parametres import get_penalite_par_jour
        from app.lecteurs import obtenir_lecteur
        penalite_j = get_penalite_par_jour()
        tous = emprunts.lister_emprunts_en_cours()
        en_retard = [e for e in tous if e["en_retard"]]

        self.table.setRowCount(len(en_retard))
        total_penalites = 0
        for i, e in enumerate(en_retard):
            pen = e["jours_retard_actuel"] * penalite_j
            total_penalites += pen
            nom = f"{e['lecteur_nom']} {e.get('lecteur_prenom') or ''}".strip()
            lec = obtenir_lecteur(e["lecteur_id"])
            tel = lec["telephone"] if lec else "—"

            self.table.setItem(i, 0, _item(e["id"]))
            self.table.setItem(i, 1, _item(e["livre_titre"], gras=True))
            self.table.setItem(i, 2, _item(nom, rouge=True, gras=True))
            self.table.setItem(i, 3, _item(tel))
            self.table.setItem(i, 4, _item(e["date_retour_prevue"]))
            self.table.setItem(i, 5, _item(e["jours_retard_actuel"], rouge=True))
            self.table.setItem(i, 6, _item(f"{pen:.0f}", rouge=True, gras=True))

        nb = len(en_retard)
        if nb:
            self.label_total.setText(f"{nb} emprunt(s) en retard  —  Total pénalités : {total_penalites:.0f} FCFA")
            self.label_total.setStyleSheet("color: #c53030; font-size: 13px;")
        else:
            self.label_total.setText("Aucun retard en cours.")
            self.label_total.setStyleSheet("color: #276749; font-size: 13px; font-weight: bold;")


# ─────────────────────────────────────────────
#  Onglet Trésorerie
# ─────────────────────────────────────────────

MOIS_NOMS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
             "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


class OngletTresorerie(QWidget):
    COLS = ["Date", "Type", "Lecteur", "Référence", "Note", "Montant (FCFA)"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(_titre_section("Trésorerie"))

        # Filtres
        filtres = QHBoxLayout()
        filtres.addWidget(QLabel("Année :"))
        self.combo_annee = QComboBox()
        self.combo_annee.setMinimumWidth(90)
        filtres.addWidget(self.combo_annee)
        filtres.addSpacing(12)
        filtres.addWidget(QLabel("Mois :"))
        self.combo_mois = QComboBox()
        self.combo_mois.addItem("Tous les mois", 0)
        for i, nom in enumerate(MOIS_NOMS, 1):
            self.combo_mois.addItem(nom, i)
        self.combo_mois.setCurrentIndex(QDate.currentDate().month())
        filtres.addWidget(self.combo_mois)
        filtres.addSpacing(8)
        btn_filtrer = _btn("Afficher", "#2b6cb0")
        btn_filtrer.clicked.connect(self.charger)
        filtres.addWidget(btn_filtrer)
        filtres.addStretch()
        btn_pdf = _btn("Rapport PDF", "#276749")
        btn_pdf.clicked.connect(self.generer_rapport_pdf)
        filtres.addWidget(btn_pdf)
        layout.addLayout(filtres)

        self.table = _table(self.COLS)
        layout.addWidget(self.table)

        # Résumé
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        resume_layout = QHBoxLayout()
        self.lbl_abo = self._lbl_resume("Abonnements", "#2b6cb0")
        self.lbl_pen = self._lbl_resume("Pénalités", "#c53030")
        self.lbl_total = self._lbl_resume("TOTAL", "#276749")
        resume_layout.addWidget(self.lbl_abo)
        resume_layout.addWidget(self.lbl_pen)
        resume_layout.addStretch()
        resume_layout.addWidget(self.lbl_total)
        layout.addLayout(resume_layout)

        self._charger_annees()
        self.charger()

    def _lbl_resume(self, titre, couleur):
        w = QLabel()
        w.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        w.setStyleSheet(f"color: {couleur}; background: white; border-radius: 8px; padding: 8px 18px; border: 2px solid {couleur};")
        w.setProperty("_titre", titre)
        w.setText(f"{titre} : 0 FCFA")
        return w

    def _charger_annees(self):
        annees = tresorerie.annees_disponibles()
        annee_courante = str(QDate.currentDate().year())
        self.combo_annee.clear()
        if not annees or annee_courante not in annees:
            annees = [annee_courante] + [a for a in annees if a != annee_courante]
        for a in annees:
            self.combo_annee.addItem(a, int(a))
        idx = self.combo_annee.findData(QDate.currentDate().year())
        if idx >= 0:
            self.combo_annee.setCurrentIndex(idx)

    def charger(self):
        annee = self.combo_annee.currentData()
        mois = self.combo_mois.currentData()
        lignes = tresorerie.lister(annee=annee, mois=mois if mois else None)
        res = tresorerie.resume(annee=annee, mois=mois if mois else None)

        self.table.setRowCount(len(lignes))
        TYPES = {"abonnement": "Abonnement", "penalite": "Pénalité", "autre": "Autre"}
        for i, l in enumerate(lignes):
            rouge = l["type"] == "penalite"
            vert = l["type"] == "abonnement"
            it_type = QTableWidgetItem(TYPES.get(l["type"], l["type"]))
            if rouge:
                it_type.setForeground(QColor("#c53030"))
            elif vert:
                it_type.setForeground(QColor("#276749"))
            it_type.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(i, 0, _item(l["date"]))
            self.table.setItem(i, 1, it_type)
            self.table.setItem(i, 2, _item((l.get("lecteur_nom") or "—").strip()))
            self.table.setItem(i, 3, _item(l.get("reference")))
            self.table.setItem(i, 4, _item(l.get("note")))
            self.table.setItem(i, 5, _item(f"{l['montant']:.0f}", gras=True))

        self.lbl_abo.setText(f"Abonnements : {res['abonnements']:.0f} FCFA")
        self.lbl_pen.setText(f"Pénalités : {res['penalites']:.0f} FCFA")
        self.lbl_total.setText(f"TOTAL : {res['total']:.0f} FCFA")

    def generer_rapport_pdf(self):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from app.parametres import get_parametre
        import os

        annee = self.combo_annee.currentData()
        mois = self.combo_mois.currentData()
        mois_nom = MOIS_NOMS[mois - 1] if mois else "Tous mois"
        lignes = tresorerie.lister(annee=annee, mois=mois if mois else None)
        res = tresorerie.resume(annee=annee, mois=mois if mois else None)

        dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
        os.makedirs(dossier, exist_ok=True)
        nom_fichier = f"rapport_{annee}_{mois:02d}.pdf" if mois else f"rapport_{annee}.pdf"
        chemin = os.path.join(dossier, nom_fichier)

        nom_bib = get_parametre("nom_bibliotheque", "Bibliothèque")
        devise = get_parametre("devise", "FCFA")
        styles = getSampleStyleSheet()
        style_titre = ParagraphStyle("T", parent=styles["Title"], fontSize=16, spaceAfter=4)
        style_sous = ParagraphStyle("S", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
        style_n = styles["Normal"]

        doc = SimpleDocTemplate(chemin, pagesize=A4,
                                topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        elems = [
            Paragraph(nom_bib, style_titre),
            Paragraph(f"Rapport de trésorerie — {mois_nom} {annee}", style_sous),
            Spacer(1, 0.8*cm),
        ]

        # Résumé
        data_res = [
            ["Encaissements abonnements", f"{res['abonnements']:.0f} {devise}"],
            ["Pénalités de retard",       f"{res['penalites']:.0f} {devise}"],
            ["Autres recettes",           f"{res['autre']:.0f} {devise}"],
            ["TOTAL ENCAISSÉ",            f"{res['total']:.0f} {devise}"],
        ]
        t_res = Table(data_res, colWidths=[10*cm, 5*cm])
        t_res.setStyle(TableStyle([
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("LINEBELOW", (0,0), (-1,-2), 0.5, colors.lightgrey),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e6f4ea")),
        ]))
        elems += [Paragraph("Résumé", styles["Heading3"]), t_res, Spacer(1, 0.8*cm)]

        # Détail des transactions
        if lignes:
            TYPES = {"abonnement": "Abonnement", "penalite": "Pénalité", "autre": "Autre"}
            data_det = [["Date", "Type", "Lecteur", "Référence", "Montant"]]
            for l in lignes:
                data_det.append([
                    l["date"],
                    TYPES.get(l["type"], l["type"]),
                    (l.get("lecteur_nom") or "—").strip(),
                    l.get("reference") or "—",
                    f"{l['montant']:.0f} {devise}",
                ])
            t_det = Table(data_det, colWidths=[2.5*cm, 2.8*cm, 4*cm, 3.5*cm, 2.7*cm])
            t_det.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2b6cb0")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f7fafc")]),
                ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ]))
            elems += [Paragraph("Détail des transactions", styles["Heading3"]), t_det]

        doc.build(elems)
        QMessageBox.information(self, "Rapport généré",
            f"Rapport PDF enregistré :\n{chemin}")


# ─────────────────────────────────────────────
#  Fenêtre principale
# ─────────────────────────────────────────────

class DialogueLicence(QDialog):
    """Affiché quand la licence est absente, expirée ou invalide."""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Licence requise")
        self.setMinimumWidth(500)
        self.setFixedWidth(500)
        self.setStyleSheet("background-color: #f0f4f8;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        titre = QLabel("Activation requise")
        titre.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        titre.setStyleSheet("color: #c53030;")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titre)

        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setStyleSheet(
            "background: #fff5f5; border: 1px solid #fed7d7; border-radius: 8px;"
            "padding: 12px; color: #742a2a; font-size: 13px;"
        )
        layout.addWidget(lbl_msg)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        layout.addWidget(QLabel("Chargez votre fichier de licence (.key) fourni par le développeur :"))

        self.champ_chemin = QLineEdit()
        self.champ_chemin.setPlaceholderText("Chemin vers le fichier licence.key…")
        self.champ_chemin.setReadOnly(True)
        layout.addWidget(self.champ_chemin)

        btn_parcourir = _btn("Parcourir…", "#2b6cb0")
        btn_parcourir.clicked.connect(self._parcourir)
        layout.addWidget(btn_parcourir)

        contact = QLabel(
            "Pour obtenir une licence, contactez :\n"
            "Dr TONDE Salifou  —  tonde410@gmail.com  —  +226 74 64 13 06"
        )
        contact.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contact.setStyleSheet("color: #4a5568; font-size: 12px; font-style: italic;")
        layout.addWidget(contact)

        self.btn_activer = _btn("Activer", "#276749")
        self.btn_activer.setEnabled(False)
        self.btn_activer.clicked.connect(self._activer)
        layout.addWidget(self.btn_activer)

        btn_quitter = _btn("Quitter l'application", "#718096")
        btn_quitter.clicked.connect(lambda: sys.exit(0))
        layout.addWidget(btn_quitter)

        self._chemin = None

    def _parcourir(self):
        from PySide6.QtWidgets import QFileDialog
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier de licence", "", "Fichier licence (*.key)"
        )
        if chemin:
            self._chemin = chemin
            self.champ_chemin.setText(chemin)
            self.btn_activer.setEnabled(True)

    def _activer(self):
        try:
            installer_licence(self._chemin)
            verifier_licence()
            QMessageBox.information(self, "Activé",
                "Licence activée avec succès !\nL'application va démarrer.")
            self.accept()
        except LicenceExpiree as e:
            QMessageBox.critical(self, "Licence expirée",
                f"Cette licence a expiré le {e.expiration}.\nDemandez un renouvellement.")
        except LicenceInvalide as e:
            QMessageBox.critical(self, "Licence invalide", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


class DialogueAPropos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos")
        self.setMinimumWidth(460)
        self.setFixedWidth(460)
        self.setStyleSheet("background-color: #f0f4f8;")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        titre = QLabel("Gestion de Bibliothèque")
        titre.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titre.setStyleSheet("color: #2b6cb0;")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titre)

        version = QLabel("Version 1.0")
        version.setStyleSheet("color: #718096; font-size: 12px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        desc = QLabel(
            "Application de gestion de bibliothèque permettant de gérer\n"
            "les livres, lecteurs, abonnements, emprunts et la trésorerie.\n"
            "Génération automatique de reçus PDF et rapports mensuels."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #4a5568; font-size: 12px; line-height: 1.6;")
        layout.addWidget(desc)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        dev_label = QLabel("Développeur")
        dev_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        dev_label.setStyleSheet("color: #2b6cb0;")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dev_label)

        infos = [
            ("👤", "Dr TONDE Salifou"),
            ("✉", "tonde410@gmail.com"),
            ("📞", "+226 74 64 13 06"),
        ]
        for icone, texte in infos:
            ligne = QLabel(f"{icone}  {texte}")
            ligne.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ligne.setStyleSheet("font-size: 13px; color: #2d3748; padding: 2px;")
            layout.addWidget(ligne)

        layout.addSpacing(8)
        btn = _btn("Fermer", "#2b6cb0")
        btn.clicked.connect(self.accept)
        btn.setFixedWidth(120)
        h = QHBoxLayout()
        h.addStretch(); h.addWidget(btn); h.addStretch()
        layout.addLayout(h)


class FenetrePrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion de Bibliothèque")
        self.setMinimumSize(960, 640)

        actualiser_statuts_abonnements()

        self.onglets = QTabWidget()
        self.onglets.addTab(OngletLivres(), "  Livres  ")
        self.onglets.addTab(OngletLecteurs(), "  Lecteurs & Abonnements  ")
        self.onglets.addTab(OngletEmprunts(), "  Emprunts  ")
        self.onglets.addTab(OngletRetards(), "  Retards  ")
        self.onglets.addTab(OngletTresorerie(), "  Trésorerie  ")
        self.setCentralWidget(self.onglets)

        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(
            "QMenuBar { background: #2b6cb0; color: white; font-size: 13px; padding: 2px; }"
            "QMenuBar::item:selected { background: #1a4a8a; border-radius: 4px; }"
            "QMenu { background: white; color: #2d3748; border: 1px solid #e2e8f0; }"
            "QMenu::item:selected { background: #ebf8ff; color: #2b6cb0; }"
        )
        menu_aide = menu_bar.addMenu("  ?  Aide  ")
        action_apropos = menu_aide.addAction("À propos de l'application")
        action_apropos.triggered.connect(lambda: DialogueAPropos(self).exec())

        # Horloge temps réel — coin supérieur droit de la barre de menu
        self._lbl_horloge = QLabel()
        self._lbl_horloge.setStyleSheet(
            "color: white; font-size: 12px; padding: 0 14px; font-family: Consolas, monospace; letter-spacing: 0.5px;"
        )
        self._maj_horloge()
        self._timer_horloge = QTimer(self)
        self._timer_horloge.timeout.connect(self._maj_horloge)
        self._timer_horloge.start(1000)
        menu_bar.setCornerWidget(self._lbl_horloge, Qt.Corner.TopRightCorner)

        barre = QStatusBar()
        barre.showMessage("Bibliothèque — Prêt")
        self.setStatusBar(barre)


    def _maj_horloge(self):
        now = QDateTime.currentDateTime()
        self._lbl_horloge.setText(now.toString("ddd dd/MM/yyyy   HH:mm:ss"))


def verifier_ou_demander_licence(app):
    """Vérifie la licence. Si absente/expirée/invalide, affiche le dialogue d'activation."""
    while True:
        try:
            donnees = verifier_licence()
            return donnees
        except LicenceAbsente:
            msg = "Aucune licence trouvée.\nVeuillez charger votre fichier de licence."
        except LicenceExpiree as e:
            msg = f"Votre licence a expiré le {e.expiration}.\nVeuillez renouveler votre licence."
        except LicenceInvalide as e:
            msg = f"Licence invalide : {e}\nVeuillez charger un fichier de licence valide."

        dlg = DialogueLicence(msg)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)


def main():
    appliquer_migrations()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Vérification de la licence avant d'afficher l'interface
    donnees_licence = verifier_ou_demander_licence(app)

    fenetre = FenetrePrincipale()

    # Afficher les infos de licence dans la barre de statut
    jours = jours_restants()
    if jours is not None:
        couleur = "#c53030" if jours <= 7 else "white"
        fenetre.statusBar().setStyleSheet(
            f"QStatusBar {{ background: #2b6cb0; color: {couleur}; font-size: 12px; padding: 2px 8px; }}"
        )
        avertissement = "  ⚠ RENOUVELLEMENT URGENT" if jours <= 7 else ""
        fenetre.statusBar().showMessage(
            f"Bibliothèque — Prêt  |  "
            f"Licence : {donnees_licence['client']}  |  "
            f"Expire le {donnees_licence['expiration']} ({jours} jour(s) restant(s))"
            f"{avertissement}"
        )

    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
