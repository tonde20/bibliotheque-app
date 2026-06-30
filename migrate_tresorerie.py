from app.db import get_connection

conn = get_connection()
cols = [r[1] for r in conn.execute("PRAGMA table_info(Tresorerie)").fetchall()]

if not cols:
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
    conn.commit()
    print("Table Tresorerie créée.")

    # Importer les encaissements existants depuis Recus
    conn.execute("""
        INSERT INTO Tresorerie (date, type, montant, reference, lecteur_id, note)
        SELECT r.date_emission, 'abonnement', r.montant, r.numero_recu,
               a.lecteur_id, 'Import historique'
        FROM Recus r
        JOIN Abonnements a ON a.id = r.abonnement_id
    """)
    # Importer les pénalités existantes
    conn.execute("""
        INSERT INTO Tresorerie (date, type, montant, reference, lecteur_id, note)
        SELECT e.date_retour_reelle, 'penalite', e.penalite,
               'Emprunt #' || e.id, e.lecteur_id, 'Import historique'
        FROM Emprunts e
        WHERE e.penalite > 0 AND e.date_retour_reelle IS NOT NULL
    """)
    conn.commit()
    print("Historique importé dans Tresorerie.")
else:
    print("Table Tresorerie déjà existante.")

conn.close()
