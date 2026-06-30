-- ============================================================
-- Schéma de base de données — Gestion de Bibliothèque
-- SQLite
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Table : Livres
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Livres (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titre           TEXT NOT NULL,
    auteur          TEXT,
    isbn            TEXT,
    categorie       TEXT,
    quantite_total      INTEGER NOT NULL DEFAULT 1,
    quantite_disponible INTEGER NOT NULL DEFAULT 1,
    statut          TEXT NOT NULL DEFAULT 'disponible'
                        CHECK (statut IN ('disponible', 'sorti', 'perdu', 'retire')),
    date_ajout      TEXT NOT NULL DEFAULT (date('now'))
);

-- ------------------------------------------------------------
-- Table : Lecteurs (les abonnés de la bibliothèque)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Lecteurs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             TEXT NOT NULL,
    prenom          TEXT,
    telephone       TEXT,
    email           TEXT,
    adresse         TEXT,
    date_inscription TEXT NOT NULL DEFAULT (date('now'))
);

-- ------------------------------------------------------------
-- Table : TypesAbonnement
-- Catalogue des formules proposées (modifiable sans toucher au code)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS TypesAbonnement (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             TEXT NOT NULL,            -- ex : "1 mois", "3 mois", "1 an"
    duree_jours     INTEGER NOT NULL,
    prix            REAL NOT NULL
);

-- ------------------------------------------------------------
-- Table : Abonnements
-- Un abonnement = un lecteur qui souscrit à une formule, à une date donnée
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Abonnements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    lecteur_id          INTEGER NOT NULL,
    type_abonnement_id  INTEGER NOT NULL,
    date_debut          TEXT NOT NULL DEFAULT (date('now')),
    date_fin            TEXT NOT NULL,        -- calculée : date_debut + duree_jours
    montant_paye        REAL NOT NULL,
    statut              TEXT NOT NULL DEFAULT 'actif'
                            CHECK (statut IN ('actif', 'expire', 'annule')),
    FOREIGN KEY (lecteur_id) REFERENCES Lecteurs(id),
    FOREIGN KEY (type_abonnement_id) REFERENCES TypesAbonnement(id)
);

-- ------------------------------------------------------------
-- Table : Recus
-- Un reçu est émis à chaque encaissement d'abonnement
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Recus (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    abonnement_id   INTEGER NOT NULL,
    numero_recu     TEXT NOT NULL UNIQUE,     -- ex : REC-2026-00001
    date_emission   TEXT NOT NULL DEFAULT (date('now')),
    montant         REAL NOT NULL,
    duree_jours     INTEGER NOT NULL,
    chemin_pdf      TEXT,                     -- chemin du fichier PDF généré
    FOREIGN KEY (abonnement_id) REFERENCES Abonnements(id)
);

-- ------------------------------------------------------------
-- Table : Emprunts
-- Sortie d'un livre par un lecteur, et son retour
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Emprunts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    livre_id            INTEGER NOT NULL,
    lecteur_id          INTEGER NOT NULL,
    date_sortie         TEXT NOT NULL DEFAULT (date('now')),
    date_retour_prevue  TEXT NOT NULL,
    date_retour_reelle  TEXT,                 -- NULL tant que le livre n'est pas rendu
    statut              TEXT NOT NULL DEFAULT 'en_cours'
                            CHECK (statut IN ('en_cours', 'rendu', 'rendu_en_retard')),
    jours_retard        INTEGER NOT NULL DEFAULT 0,
    penalite            REAL NOT NULL DEFAULT 0,
    total               REAL NOT NULL DEFAULT 0,   -- penalite + frais éventuels
    FOREIGN KEY (livre_id) REFERENCES Livres(id),
    FOREIGN KEY (lecteur_id) REFERENCES Lecteurs(id)
);

-- ------------------------------------------------------------
-- Table : Parametres
-- Paramètres modifiables sans changer le code (clé / valeur)
-- ex : penalite_par_jour, duree_emprunt_defaut_jours
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Parametres (
    cle     TEXT PRIMARY KEY,
    valeur  TEXT NOT NULL
);

-- ------------------------------------------------------------
-- Index utiles pour les recherches fréquentes
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_livres_statut ON Livres(statut);
CREATE INDEX IF NOT EXISTS idx_emprunts_statut ON Emprunts(statut);
CREATE INDEX IF NOT EXISTS idx_abonnements_statut ON Abonnements(statut);
CREATE INDEX IF NOT EXISTS idx_lecteurs_nom ON Lecteurs(nom);
