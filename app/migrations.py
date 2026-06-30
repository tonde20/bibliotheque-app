"""
migrations.py
Système de migrations automatiques de la base de données.
Chaque migration est identifiée par un nom unique et n'est appliquée qu'une seule fois.
Appelé au démarrage de l'application.
"""

from .db import get_connection


def _assurer_table_migrations(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Migrations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL UNIQUE,
            appliquee_le TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _deja_appliquee(conn, nom):
    return conn.execute(
        "SELECT 1 FROM Migrations WHERE nom = ?", (nom,)
    ).fetchone() is not None


def _marquer(conn, nom):
    conn.execute("INSERT INTO Migrations (nom) VALUES (?)", (nom,))
    conn.commit()


# ─── Liste des migrations dans l'ordre ───────────────────────────────────────

def _m000_schema_initial(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS Livres (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            titre               TEXT NOT NULL,
            auteur              TEXT,
            isbn                TEXT,
            categorie           TEXT,
            quantite_total      INTEGER NOT NULL DEFAULT 1,
            quantite_disponible INTEGER NOT NULL DEFAULT 1,
            statut              TEXT NOT NULL DEFAULT 'disponible'
                                    CHECK (statut IN ('disponible', 'sorti', 'perdu', 'retire')),
            date_ajout          TEXT NOT NULL DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS Lecteurs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nom              TEXT NOT NULL,
            prenom           TEXT,
            telephone        TEXT,
            email            TEXT,
            adresse          TEXT,
            date_inscription TEXT NOT NULL DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS TypesAbonnement (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL,
            duree_jours INTEGER NOT NULL,
            prix        REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Abonnements (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            lecteur_id         INTEGER NOT NULL,
            type_abonnement_id INTEGER NOT NULL,
            date_debut         TEXT NOT NULL DEFAULT (date('now')),
            date_fin           TEXT NOT NULL,
            montant_paye       REAL NOT NULL,
            statut             TEXT NOT NULL DEFAULT 'actif'
                                   CHECK (statut IN ('actif', 'expire', 'annule')),
            FOREIGN KEY (lecteur_id) REFERENCES Lecteurs(id),
            FOREIGN KEY (type_abonnement_id) REFERENCES TypesAbonnement(id)
        );
        CREATE TABLE IF NOT EXISTS Recus (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            abonnement_id INTEGER NOT NULL,
            numero_recu   TEXT NOT NULL UNIQUE,
            date_emission TEXT NOT NULL DEFAULT (date('now')),
            montant       REAL NOT NULL,
            duree_jours   INTEGER NOT NULL,
            chemin_pdf    TEXT,
            FOREIGN KEY (abonnement_id) REFERENCES Abonnements(id)
        );
        CREATE TABLE IF NOT EXISTS Emprunts (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            livre_id           INTEGER NOT NULL,
            lecteur_id         INTEGER NOT NULL,
            date_sortie        TEXT NOT NULL DEFAULT (date('now')),
            date_retour_prevue TEXT NOT NULL,
            date_retour_reelle TEXT,
            statut             TEXT NOT NULL DEFAULT 'en_cours'
                                   CHECK (statut IN ('en_cours', 'rendu', 'rendu_en_retard')),
            jours_retard       INTEGER NOT NULL DEFAULT 0,
            penalite           REAL NOT NULL DEFAULT 0,
            total              REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (livre_id) REFERENCES Livres(id),
            FOREIGN KEY (lecteur_id) REFERENCES Lecteurs(id)
        );
        CREATE TABLE IF NOT EXISTS Parametres (
            cle    TEXT PRIMARY KEY,
            valeur TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_livres_statut ON Livres(statut);
        CREATE INDEX IF NOT EXISTS idx_emprunts_statut ON Emprunts(statut);
        CREATE INDEX IF NOT EXISTS idx_abonnements_statut ON Abonnements(statut);
        CREATE INDEX IF NOT EXISTS idx_lecteurs_nom ON Lecteurs(nom);
    """)
    # Données par défaut seulement si tables vides
    if conn.execute("SELECT COUNT(*) FROM TypesAbonnement").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO TypesAbonnement (nom, duree_jours, prix) VALUES (?, ?, ?)",
            [("1 semaine", 7, 500), ("2 semaines", 14, 900),
             ("1 mois", 30, 2000), ("3 mois", 90, 5000),
             ("6 mois", 180, 9000), ("1 an", 365, 15000)]
        )
    if conn.execute("SELECT COUNT(*) FROM Parametres").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO Parametres (cle, valeur) VALUES (?, ?)",
            [("penalite_par_jour_retard", "100"),
             ("duree_emprunt_defaut_jours", "14"),
             ("devise", "FCFA"),
             ("nom_bibliotheque", "Bibliothèque")]
        )
    conn.commit()


def _m001_quantites_livres(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(Livres)").fetchall()]
    if "quantite_total" not in cols:
        conn.execute("ALTER TABLE Livres ADD COLUMN quantite_total INTEGER NOT NULL DEFAULT 1")
    if "quantite_disponible" not in cols:
        conn.execute("ALTER TABLE Livres ADD COLUMN quantite_disponible INTEGER NOT NULL DEFAULT 1")
        conn.execute("UPDATE Livres SET quantite_disponible = 0 WHERE statut = 'sorti'")
    conn.commit()


def _m002_tresorerie(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Tresorerie (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL DEFAULT (date('now')),
            type        TEXT NOT NULL CHECK (type IN ('abonnement', 'penalite', 'autre')),
            montant     REAL NOT NULL,
            reference   TEXT,
            lecteur_id  INTEGER,
            note        TEXT,
            FOREIGN KEY (lecteur_id) REFERENCES Lecteurs(id)
        )
    """)
    # Importer l'historique existant s'il n'y a rien encore
    nb = conn.execute("SELECT COUNT(*) FROM Tresorerie").fetchone()[0]
    if nb == 0:
        conn.execute("""
            INSERT INTO Tresorerie (date, type, montant, reference, lecteur_id, note)
            SELECT r.date_emission, 'abonnement', r.montant, r.numero_recu,
                   a.lecteur_id, 'Import historique'
            FROM Recus r
            JOIN Abonnements a ON a.id = r.abonnement_id
        """)
        conn.execute("""
            INSERT INTO Tresorerie (date, type, montant, reference, lecteur_id, note)
            SELECT e.date_retour_reelle, 'penalite', e.penalite,
                   'Emprunt #' || e.id, e.lecteur_id, 'Import historique'
            FROM Emprunts e
            WHERE e.penalite > 0 AND e.date_retour_reelle IS NOT NULL
        """)
    conn.commit()


def _m003_types_abonnement_semaines(conn):
    existants = [r[0] for r in conn.execute("SELECT nom FROM TypesAbonnement").fetchall()]
    if "1 semaine" not in existants:
        conn.execute("INSERT INTO TypesAbonnement (nom, duree_jours, prix) VALUES ('1 semaine', 7, 500)")
    if "2 semaines" not in existants:
        conn.execute("INSERT INTO TypesAbonnement (nom, duree_jours, prix) VALUES ('2 semaines', 14, 900)")
    conn.commit()


def _m004_wal_mode(conn):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.commit()


def _m005_nom_bibliotheque(conn):
    conn.execute(
        "INSERT INTO Parametres (cle, valeur) VALUES (?, ?) "
        "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
        ("nom_bibliotheque", "Bibliothèque Darous-salam"),
    )
    conn.commit()


def _m006_lecteur_photo(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(Lecteurs)").fetchall()]
    if "photo" not in cols:
        conn.execute("ALTER TABLE Lecteurs ADD COLUMN photo TEXT")
    conn.commit()


# ─── Registre des migrations ──────────────────────────────────────────────────

MIGRATIONS = [
    ("000_schema_initial",            _m000_schema_initial),
    ("001_quantites_livres",          _m001_quantites_livres),
    ("002_tresorerie",                _m002_tresorerie),
    ("003_types_abonnement_semaines", _m003_types_abonnement_semaines),
    ("004_wal_mode",                  _m004_wal_mode),
    ("005_nom_bibliotheque",          _m005_nom_bibliotheque),
    ("006_lecteur_photo",             _m006_lecteur_photo),
]


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def appliquer_migrations():
    """À appeler une seule fois au démarrage de l'application."""
    conn = get_connection()
    try:
        _assurer_table_migrations(conn)
        for nom, fn in MIGRATIONS:
            if not _deja_appliquee(conn, nom):
                fn(conn)
                _marquer(conn, nom)
    finally:
        conn.close()
