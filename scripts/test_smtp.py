#!/usr/bin/env python3
"""Envoie un email de test via le SMTP cPanel de contact@lumenjuris.com.

A LANCER SUR VOTRE MACHINE, pas dans l'environnement Claude Code en ligne :
les ports SMTP (25, 465, 587, 2525) y sont bloques par la politique reseau,
et le domaine lumenjuris.com n'est pas joignable non plus en HTTPS.

    export SMTP_PASS_LUMEN='le mot de passe cPanel'
    python3 scripts/test_smtp.py --to edouardlopro@gmail.com --dry-run
    python3 scripts/test_smtp.py --to edouardlopro@gmail.com

Le mot de passe est lu depuis une variable d'environnement : ne le passez pas
en argument (il resterait dans l'historique du shell) et ne l'ecrivez pas dans
un fichier du depot.

Une fois le message recu, ouvrez « Afficher l'original » dans Gmail et
verifiez que SPF, DKIM et DMARC sont tous en PASS. C'est ce qui determine si
vos envois arrivent en boite de reception plutot qu'en spam.
"""

import argparse
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

SERVEUR_DEFAUT = "mail.lumenjuris.com"
EXPEDITEUR_DEFAUT = "contact@lumenjuris.com"

CORPS = """\
Ceci est un email de test, envoye pour verifier la configuration d'envoi.

A verifier a la reception :
  - expediteur affiche : {expediteur}
  - emplacement : Reception (et non Spam ou Promotions)
  - « Afficher l'original » : SPF, DKIM et DMARC doivent etre en PASS

Aucune action n'est attendue de votre part.
"""


def main():
    p = argparse.ArgumentParser(description="Envoi d'un email de test via SMTP cPanel.")
    p.add_argument("--to", required=True, help="Destinataire unique.")
    p.add_argument("--from", dest="expediteur", default=EXPEDITEUR_DEFAUT)
    p.add_argument("--serveur", default=SERVEUR_DEFAUT)
    p.add_argument("--port", type=int, default=465,
                   help="465 = SSL direct (defaut), 587 = STARTTLS.")
    p.add_argument("--user", default=None,
                   help="Identifiant SMTP (defaut : identique a --from).")
    p.add_argument("--sujet", default="[TEST] Verification d'envoi Lumen Juris")
    p.add_argument("--env-var", default="SMTP_PASS_LUMEN")
    p.add_argument("--dry-run", action="store_true",
                   help="Tester la connexion et l'authentification, sans envoyer.")
    args = p.parse_args()

    mot_de_passe = os.environ.get(args.env_var)
    if not mot_de_passe:
        sys.exit(
            f"Variable {args.env_var} absente.\n"
            f"  export {args.env_var}='le mot de passe cPanel'\n"
            "Ne le passez pas en argument de ligne de commande."
        )

    utilisateur = args.user or args.expediteur

    msg = EmailMessage()
    msg["From"] = args.expediteur
    msg["To"] = args.to
    msg["Subject"] = args.sujet
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=args.expediteur.split("@")[-1])
    msg.set_content(CORPS.format(expediteur=args.expediteur))

    print("-" * 60)
    print(f"  Serveur      : {args.serveur}:{args.port}")
    print(f"  Utilisateur  : {utilisateur}")
    print(f"  Expediteur   : {args.expediteur}")
    print(f"  Destinataire : {args.to}")
    print("-" * 60)

    contexte = ssl.create_default_context()
    try:
        if args.port == 465:
            serveur = smtplib.SMTP_SSL(args.serveur, args.port, context=contexte, timeout=30)
        else:
            serveur = smtplib.SMTP(args.serveur, args.port, timeout=30)
            serveur.starttls(context=contexte)
        with serveur:
            serveur.login(utilisateur, mot_de_passe)
            print("Connexion et authentification : OK")
            if args.dry_run:
                print("--dry-run : rien n'a ete envoye.")
                return
            serveur.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        sys.exit("Authentification refusee : verifiez l'identifiant et le mot de passe cPanel.")
    except (smtplib.SMTPException, OSError, ssl.SSLError) as e:
        sys.exit(f"Echec : {type(e).__name__} — {e}")

    print(f"\nEnvoye a {args.to}.")
    print("Verifiez la reception, puis « Afficher l'original » pour SPF/DKIM/DMARC.")


if __name__ == "__main__":
    main()
