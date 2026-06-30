from app.db import get_connection

conn = get_connection()
cols = [r[1] for r in conn.execute("PRAGMA table_info(Livres)").fetchall()]

if "quantite_total" not in cols:
    conn.execute("ALTER TABLE Livres ADD COLUMN quantite_total INTEGER NOT NULL DEFAULT 1")
    print("Colonne quantite_total ajoutée.")

if "quantite_disponible" not in cols:
    conn.execute("ALTER TABLE Livres ADD COLUMN quantite_disponible INTEGER NOT NULL DEFAULT 1")
    conn.execute("UPDATE Livres SET quantite_disponible = 0 WHERE statut = 'sorti'")
    print("Colonne quantite_disponible ajoutée.")

conn.commit()
conn.close()
print("Migration terminée.")
