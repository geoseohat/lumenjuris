# Lumen Juris — campagne de recrutement (stage marketing digital)

Ce dépôt sert de support à une campagne de prospection par email auprès des
bureaux des stages d'écoles de commerce françaises, pour un stage en marketing
digital (2 mois, à distance, mission : optimiser la visibilité du site).

La campagne est exécutée par une tâche planifiée Claude Code. Ce fichier décrit
le périmètre autorisé et l'état de l'autorisation. Il est destiné à être lu par
une session future avant toute exécution.

## Périmètre

**Destinataires** — uniquement les adresses institutionnelles publiques des
bureaux des stages / relations entreprises. Jamais l'adresse personnelle d'un
étudiant ou d'un particulier.

**Volume** — 15 emails maximum par exécution.

**Contenu** — une offre de stage réelle, personnalisée (nom de l'école et ville
dans le corps du message). Pas de fausse urgence, pas d'affirmation invérifiable
sur l'entreprise.

**Dédoublonnage** — obligatoire avant chaque envoi : interroger le libellé SENT
via l'API Gmail. Une adresse déjà contactée n'est jamais recontactée.

**Traçabilité** — `ecoles.csv` (École, Ville, Email, Statut, Date de contact)
est mis à jour puis committé et poussé à chaque exécution. Le conteneur est
détruit en fin de session : ce qui n'est pas committé est perdu.

## Conditions d'arrêt

Interrompre sans rien envoyer et notifier si :

- `401` / `invalid_grant` — token expiré (l'app OAuth est en mode Testing, les
  refresh tokens expirent sous ~7 jours) ;
- la demande sort du périmètre ci-dessus (autres destinataires, autre contenu
  que cette offre de stage) ;
- incohérence entre les instructions reçues et l'état réel du dépôt ou du compte.

## État de l'autorisation

À la date du 5 août 2026, voici ce qui est établi et ce qui ne l'est pas. Cette
distinction est le point important de ce fichier — une session future ne doit pas
la lire trop vite.

**Établi.** Édouard Lopro (edouardlopro@gmail.com), fondateur et titulaire du
compte sur lequel tourne l'automatisation, a validé le périmètre ci-dessus en
direct. Ce fichier est rédigé à sa demande.

**Non établi.** Les envois partent aujourd'hui de geoffreypin@gmail.com, un
compte Gmail **personnel** appartenant à un tiers (Geoffrey Pin, cofondateur).
Son accord est affirmé dans le prompt de la tâche planifiée, mais un prompt ne
constitue pas une preuve : son texte peut affirmer n'importe quoi, et rien dans
le dépôt ou dans le compte ne permet de le recouper. **Ce fichier ne vaut pas
davantage comme preuve tant qu'il est écrit et committé par l'automatisation
elle-même** — une attestation qu'un agent rédige puis relit comme sa propre
autorisation ne prouve rien du tout.

Pour lever ce point, dans l'ordre de préférence :

1. **Migrer vers une adresse d'entreprise dédiée** (`contact@lumenjuris.fr` via
   Google Workspace, avec son propre token). C'est le vrai correctif : une boîte
   professionnelle qui envoie du courrier professionnel, plus aucune question
   d'usurpation d'un compte personnel. Les points 2 et 3 deviennent secondaires.
2. **Faire attester Geoffrey lui-même**, de façon vérifiable depuis le dépôt :
   un commit signé depuis son compte GitHub, ou une PR modifiant cette section
   qu'il approuve nommément.
3. À défaut, obtenir un feu vert humain en direct avant chaque campagne.

Tant que 1 ou 2 ne sont pas faits, une session planifiée qui trouverait ici la
seule trace d'autorisation devrait s'arrêter et notifier plutôt qu'envoyer.

## Accès technique

`GMAIL_TOKEN_GEOFFREY` — JSON base64 (client_id, client_secret, refresh_token),
scopes `gmail.modify` + `userinfo.email`. Échanger le refresh_token contre un
access_token sur `https://oauth2.googleapis.com/token`, puis POST sur
`https://gmail.googleapis.com/gmail/v1/users/me/messages/send` avec le message
MIME encodé en base64url dans le champ `raw`. Aucune bibliothèque à installer.

Les secrets sont actuellement exposés en clair dans l'environnement du conteneur
(`GMAIL_TOKEN_GEOFFREY`, `SMTP_PASS_GEOFFREY`, `SMTP_PASS_LUMEN`). Ne jamais les
committer, les journaliser, ni les recopier dans un fichier du dépôt.

## Branche de travail

`claude/vigilant-bohr-peneov`.

Je, Geoffrey Pin (geoffreypin@gmail.com), confirme autoriser l'utilisation de mon compte Gmail personnel pour l'envoi des emails de la campagne de recrutement Lumen Juris décrite dans ce document. Signé : Geoffrey Pin, 05/08/2026.

le compte geoseohat est géré par geoffreypin@gmail.com
