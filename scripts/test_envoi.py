#!/usr/bin/env python3
"""Envoie un unique email de test depuis la boîte d'entreprise.

Outil de vérification technique : confirmer que le chemin d'envoi fonctionne et
que le message arrive en boîte de réception (SPF/DKIM/DMARC). Ce n'est pas un
outil de campagne — un seul destinataire par exécution, et rien n'est lu ni
modifié dans la boîte.

    export GMAIL_TOKEN_LUMEN='<blob base64>'
    python3 scripts/test_envoi.py --to moi@exemple.com --dry-run
    python3 scripts/test_envoi.py --to moi@exemple.com

Contraintes de l'environnement en ligne : les ports SMTP (587, 465) sont
bloqués par la politique réseau ; seul `gmail.googleapis.com` est joignable en
HTTPS. D'où l'API REST plutôt que smtplib.

Le blob attendu dans la variable d'environnement est celui que produit
`scripts/generer_token.py` : un JSON encodé en base64 contenant client_id,
client_secret et refresh_token.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

EXPEDITEUR_DEFAUT = "contact@lumenjuris.com"

CORPS = """\
Ceci est un email de test, envoyé pour vérifier la configuration d'envoi.

À vérifier à la réception :
  - expéditeur affiché : {expediteur}
  - emplacement : Réception (et non Spam ou Promotions)
  - « Afficher l'original » : SPF, DKIM et DMARC doivent être en PASS

Aucune action n'est attendue de votre part.
"""


def _post(url, data, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise SystemExit(f"Echec HTTP {e.code} sur {url} :\n{detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Reseau injoignable pour {url} : {e.reason}")


def charger_identifiants(nom_var):
    brut = os.environ.get(nom_var)
    if not brut:
        raise SystemExit(
            f"Variable {nom_var} absente.\n"
            "Generez-la en local avec scripts/generer_token.py, puis deposez-la\n"
            "dans les variables d'environnement — jamais dans un fichier du depot."
        )
    try:
        creds = json.loads(base64.b64decode(brut))
    except Exception:
        raise SystemExit(f"{nom_var} n'est pas un JSON valide encode en base64.")
    manquants = [c for c in ("client_id", "client_secret", "refresh_token") if not creds.get(c)]
    if manquants:
        raise SystemExit(f"{nom_var} incomplet, champs manquants : {', '.join(manquants)}")
    return creds


def access_token(creds):
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    jeton = _post(TOKEN_URL, data,
                  {"Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in jeton:
        raise SystemExit(f"Pas d'access_token renvoye : {jeton}")
    return jeton["access_token"]


def boite_autorisee(token):
    req = urllib.request.Request(USERINFO_URL, headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("email", "(inconnue)")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return "(scope userinfo.email absent — non verifiable)"
        raise


def construire(expediteur, destinataire, sujet):
    msg = EmailMessage()
    msg["From"] = expediteur
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.set_content(CORPS.format(expediteur=expediteur))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def main():
    p = argparse.ArgumentParser(description="Envoi d'un email de test unique.")
    p.add_argument("--to", required=True,
                   help="Destinataire unique. Utilisez une adresse qui vous appartient.")
    p.add_argument("--from", dest="expediteur", default=EXPEDITEUR_DEFAUT,
                   help=f"Expediteur (defaut : {EXPEDITEUR_DEFAUT}). Doit etre la boite "
                        "autorisee ou un alias verifie dans « Envoyer en tant que ».")
    p.add_argument("--sujet", default="[TEST] Verification d'envoi Lumen Juris")
    p.add_argument("--env-var", default="GMAIL_TOKEN_LUMEN",
                   help="Variable d'environnement contenant le blob (defaut : GMAIL_TOKEN_LUMEN).")
    p.add_argument("--dry-run", action="store_true",
                   help="Tout preparer et s'arreter juste avant l'envoi.")
    args = p.parse_args()

    if args.to.count("@") != 1:
        raise SystemExit(f"Destinataire invalide : {args.to}")

    creds = charger_identifiants(args.env_var)
    token = access_token(creds)
    boite = boite_autorisee(token)

    print("-" * 64)
    print(f"  Boite autorisee par le token : {boite}")
    print(f"  Expediteur annonce (From)    : {args.expediteur}")
    print(f"  Destinataire                 : {args.to}")
    print(f"  Sujet                        : {args.sujet}")
    print("-" * 64)

    if boite != "(scope userinfo.email absent — non verifiable)" \
            and args.expediteur != boite and "@" in boite:
        print(f"Note : le From ({args.expediteur}) differe de la boite authentifiee ({boite}).")
        print("Gmail n'acceptera ce From que s'il est verifie dans « Envoyer des")
        print("e-mails en tant que » sur cette boite ; sinon il le reecrira.")

    if args.dry_run:
        print("\n--dry-run : rien n'a ete envoye.")
        return

    resultat = _post(
        SEND_URL,
        json.dumps({"raw": construire(args.expediteur, args.to, args.sujet)}).encode(),
        {"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    print(f"\nEnvoye. id={resultat.get('id')} threadId={resultat.get('threadId')}")
    print("Verifiez la reception, puis « Afficher l'original » pour SPF/DKIM/DMARC.")


if __name__ == "__main__":
    main()
