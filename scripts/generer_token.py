#!/usr/bin/env python3
"""Génère le token OAuth Gmail à coller dans l'environnement de la tâche planifiée.

À lancer EN LOCAL (pas dans le conteneur) : le navigateur doit s'ouvrir pour le
consentement Google, et il faut se connecter au compte expéditeur.

    python3 scripts/generer_token.py

Le script affiche un blob base64 à coller dans la variable d'environnement de la
tâche planifiée (GMAIL_TOKEN_EDOUARD, ou GMAIL_TOKEN_LUMEN le jour où la boîte
d'entreprise existe).

Prérequis côté Google Cloud Console :
  1. Créer un projet, activer l'API Gmail.
  2. Écran de consentement OAuth → type « Externe » → PUBLIER l'application.
     Si l'app reste en mode « Test », le refresh_token expire au bout de ~7 jours
     et la tâche planifiée tombera en invalid_grant.
  3. Identifiants → ID client OAuth → type « Application de bureau ».
     Récupérer client_id et client_secret, à saisir ci-dessous.
"""

import base64
import http.server
import json
import secrets
import socket
import urllib.parse
import urllib.request
import webbrowser

SCOPES = " ".join([
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
])


def port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def attendre_code(port, state_attendu):
    """Sert une page unique sur localhost et récupère le ?code= du redirect."""
    recu = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            recu.update({k: v[0] for k, v in params.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            ok = "code" in recu and recu.get("state") == state_attendu
            self.wfile.write(
                ("<h2>C'est bon, tu peux fermer cet onglet.</h2>" if ok
                 else "<h2>Echec : reponse inattendue.</h2>").encode()
            )

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", port), Handler)
    srv.handle_request()
    srv.server_close()
    return recu


def main():
    client_id = input("client_id     : ").strip()
    client_secret = input("client_secret : ").strip()
    if not client_id or not client_secret:
        raise SystemExit("client_id et client_secret sont obligatoires.")

    port = port_libre()
    redirect_uri = f"http://127.0.0.1:{port}"
    state = secrets.token_urlsafe(16)

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",       # force la delivrance d'un refresh_token
        "state": state,
    })

    print(f"\nOuverture du navigateur. Connecte-toi avec le compte EXPEDITEUR.")
    print(f"Si rien ne s'ouvre, colle cette URL :\n\n{url}\n")
    webbrowser.open(url)

    recu = attendre_code(port, state)
    if recu.get("state") != state:
        raise SystemExit("State invalide — relance le script.")
    if "code" not in recu:
        raise SystemExit(f"Pas de code recu : {recu.get('error', 'reponse vide')}")

    data = urllib.parse.urlencode({
        "code": recu["code"],
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    jeton = json.load(urllib.request.urlopen(
        urllib.request.Request("https://oauth2.googleapis.com/token", data=data)))

    refresh = jeton.get("refresh_token")
    if not refresh:
        raise SystemExit(
            "Google n'a pas renvoye de refresh_token. Revoque l'acces de l'app sur\n"
            "https://myaccount.google.com/permissions puis relance le script."
        )

    # Confirme de quelle boite il s'agit, pour eviter toute ambiguite d'expediteur.
    info = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": "Bearer " + jeton["access_token"]})))

    blob = base64.b64encode(json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh,
    }).encode()).decode()

    print("\n" + "=" * 70)
    print(f"Boite autorisee : {info.get('email')}")
    print("=" * 70)
    print("\nColle cette valeur dans la variable d'environnement de la tache :\n")
    print(blob)
    print("\nNe la commite pas, ne la colle pas dans une conversation ou un ticket.")


if __name__ == "__main__":
    main()
