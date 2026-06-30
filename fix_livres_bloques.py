from app.db import get_connection

conn = get_connection()
conn.execute("""
    UPDATE Livres
    SET statut = 'disponible',
        quantite_disponible = quantite_total - (
            SELECT COUNT(*) FROM Emprunts e
            WHERE e.livre_id = Livres.id AND e.statut = 'en_cours'
        )
    WHERE (
        SELECT COUNT(*) FROM Emprunts e
        WHERE e.livre_id = Livres.id AND e.statut = 'en_cours'
    ) < (quantite_total - quantite_disponible)
""")
nb = conn.execute("SELECT changes()").fetchone()[0]
conn.commit()
conn.close()
print(f"{nb} livre(s) corrigé(s).")
