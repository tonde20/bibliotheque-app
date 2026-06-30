"""
licence.py
Vérification de la licence au démarrage de l'application.
La clé publique est embarquée ici — la clé privée reste chez le développeur.
"""

import os
import sys
import json
import base64
from datetime import date
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

# Clé publique embarquée directement dans le code
CLE_PUBLIQUE_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1dWAdgajFW70mDFTqPcJ
9gmnmSse1Sri2Ets+mA4X8ow6vb0XfPCHV/+qd2pqRGtI7ejfc+o+jyIYz6jeS3l
RcovcD48WrWNa75HhtOA8W4by9Y1PnQlCt71PjMx3E80NGciMg+40UQnDOocJcFY
CHgEK8Mbi2Brft2MXW7Tk4/gX0q3cTGuUGg2P7AKlR9JzOuyEMctqwj4GKhaNMGq
Unt71u9Qql94S6xiKyVE1hKL09uKkoWDTMTfSpkz/ipEpIM9mqRvjDX+9e65ARyM
7BkLvE32JD5Qw988TC8Z+BcX/SSaqNthZG2YcGJy6LIosgxaQ3MdBP/ZsEjwSXUT
3wIDAQAB
-----END PUBLIC KEY-----"""

# Emplacement du fichier de licence (à côté de l'exe ou du script)
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FICHIER_LICENCE = os.path.join(_BASE, "licence.key")


class LicenceInvalide(Exception):
    pass

class LicenceExpiree(Exception):
    def __init__(self, expiration):
        self.expiration = expiration
        super().__init__(f"Licence expirée le {expiration}")

class LicenceAbsente(Exception):
    pass


def _charger_cle_publique():
    return serialization.load_pem_public_key(CLE_PUBLIQUE_PEM)


def verifier_licence():
    """
    Lit et vérifie le fichier licence.key.
    Retourne le dict des données si valide.
    Lève LicenceAbsente, LicenceInvalide ou LicenceExpiree sinon.
    """
    if not os.path.exists(FICHIER_LICENCE):
        raise LicenceAbsente()

    try:
        with open(FICHIER_LICENCE, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except Exception:
        raise LicenceInvalide("Fichier de licence illisible ou corrompu.")

    champs = ["client", "email", "type", "emission", "expiration", "signature"]
    for c in champs:
        if c not in donnees:
            raise LicenceInvalide(f"Champ manquant : {c}")

    # Vérifier la signature RSA
    message = "|".join([
        donnees["client"], donnees["email"], donnees["type"],
        donnees["emission"], donnees["expiration"]
    ]).encode("utf-8")

    try:
        signature = base64.b64decode(donnees["signature"])
        cle_pub = _charger_cle_publique()
        cle_pub.verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        raise LicenceInvalide("Signature invalide. Licence falsifiée ou corrompue.")
    except Exception as e:
        raise LicenceInvalide(f"Erreur de vérification : {e}")

    # Vérifier la date d'expiration
    try:
        expiration = date.fromisoformat(donnees["expiration"])
    except ValueError:
        raise LicenceInvalide("Date d'expiration invalide.")

    if date.today() > expiration:
        raise LicenceExpiree(donnees["expiration"])

    return donnees


def installer_licence(chemin_fichier):
    """Copie un fichier .key fourni par l'utilisateur vers l'emplacement standard."""
    import shutil
    shutil.copy2(chemin_fichier, FICHIER_LICENCE)


def jours_restants():
    """Retourne le nombre de jours avant expiration, ou None si pas de licence valide."""
    try:
        donnees = verifier_licence()
        expiration = date.fromisoformat(donnees["expiration"])
        return (expiration - date.today()).days
    except Exception:
        return None
