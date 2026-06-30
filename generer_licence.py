"""
generer_licence.py
Outil PRIVÉ — à garder sur votre machine uniquement.
Génère les clés RSA (une seule fois) puis crée des fichiers de licence
pour vos clients.

Usage : python generer_licence.py
"""

import os
import json
import base64
from datetime import date, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

CLE_PRIVEE_PATH = "cle_privee.pem"
CLE_PUBLIQUE_PATH = "cle_publique.pem"
DOSSIER_LICENCES = "licences_generees"


# ─── Gestion des clés ────────────────────────────────────────────────────────

def generer_paire_cles():
    print("Génération d'une nouvelle paire de clés RSA...")
    cle_privee = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(CLE_PRIVEE_PATH, "wb") as f:
        f.write(cle_privee.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(CLE_PUBLIQUE_PATH, "wb") as f:
        f.write(cle_privee.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    print(f"✔ Clé privée  : {CLE_PRIVEE_PATH}  (NE JAMAIS PARTAGER)")
    print(f"✔ Clé publique: {CLE_PUBLIQUE_PATH}  (à copier dans app/)")


def charger_cle_privee():
    with open(CLE_PRIVEE_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


# ─── Création d'une licence ───────────────────────────────────────────────────

def creer_licence(client, email, type_licence):
    """
    type_licence : 'mensuel' ou 'annuel'
    Génère un fichier licence.key à envoyer au client.
    """
    aujourd_hui = date.today()
    if type_licence == "mensuel":
        expiration = aujourd_hui + timedelta(days=30)
    elif type_licence == "annuel":
        expiration = aujourd_hui + timedelta(days=365)
    else:
        raise ValueError("Type invalide. Utilisez 'mensuel' ou 'annuel'.")

    donnees = {
        "client":     client,
        "email":      email,
        "type":       type_licence,
        "emission":   aujourd_hui.isoformat(),
        "expiration": expiration.isoformat(),
    }

    # Chaîne à signer : toutes les données concaténées
    message = "|".join([
        donnees["client"], donnees["email"], donnees["type"],
        donnees["emission"], donnees["expiration"]
    ]).encode("utf-8")

    cle_privee = charger_cle_privee()
    signature = cle_privee.sign(message, padding.PKCS1v15(), hashes.SHA256())
    donnees["signature"] = base64.b64encode(signature).decode("ascii")

    contenu = json.dumps(donnees, ensure_ascii=False, indent=2)

    os.makedirs(DOSSIER_LICENCES, exist_ok=True)
    nom_fichier = f"licence_{client.replace(' ', '_')}_{expiration}.key"
    chemin = os.path.join(DOSSIER_LICENCES, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)

    print(f"\n✔ Licence créée : {chemin}")
    print(f"  Client     : {client}")
    print(f"  Email      : {email}")
    print(f"  Type       : {type_licence}")
    print(f"  Émission   : {aujourd_hui}")
    print(f"  Expiration : {expiration}")
    print(f"\n→ Envoyez ce fichier au client par email.")
    return chemin


# ─── Interface console ────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("   Générateur de licences — Bibliothèque")
    print("   Dr TONDE Salifou — tonde410@gmail.com")
    print("=" * 55)

    # Générer les clés si elles n'existent pas encore
    if not os.path.exists(CLE_PRIVEE_PATH):
        print("\n⚠  Aucune clé trouvée. Génération en cours...")
        generer_paire_cles()
        print("\n⚠  IMPORTANT : sauvegardez 'cle_privee.pem' en lieu sûr.")
        print("   Sans elle, vous ne pourrez plus générer de licences.\n")
        input("Appuyez sur Entrée pour continuer...")

    while True:
        print("\n" + "-" * 55)
        print("  Nouvelle licence")
        print("-" * 55)

        client = input("  Nom du client        : ").strip()
        if not client:
            print("  ✘ Le nom est obligatoire.")
            continue

        email = input("  Email du client      : ").strip()

        print("  Type de licence      :")
        print("    1 → Mensuel  (30 jours)")
        print("    2 → Annuel   (365 jours)")
        choix = input("  Votre choix (1/2)    : ").strip()

        if choix == "1":
            type_licence = "mensuel"
        elif choix == "2":
            type_licence = "annuel"
        else:
            print("  ✘ Choix invalide. Entrez 1 ou 2.")
            continue

        try:
            creer_licence(client, email, type_licence)
        except Exception as e:
            print(f"\n  ✘ Erreur : {e}")

        print("\n" + "-" * 55)
        continuer = input("  Générer une autre licence ? (o/n) : ").strip().lower()
        if continuer != "o":
            break

    print("\nFermeture du générateur.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu.")
    input("\nAppuyez sur Entrée pour fermer...")
