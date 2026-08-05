# Prompt de la tâche planifiée — campagne de recrutement

> **Statut : non exécutable en l'état.** Ce prompt suppose une boîte
> `contact@lumenjuris.fr` et un token `GMAIL_TOKEN_LUMEN` qui n'existent pas
> encore. Voir « Prérequis » en fin de document. Tant qu'ils manquent, une
> exécution enverrait en réalité depuis un compte personnel.

---

RECRUTEMENT — Stage marketing digital, Lumen Juris

CONTEXTE
- Lumen Juris recrute un stagiaire en marketing digital (2 mois, à distance,
  mission : optimiser la visibilité du site web).
- Les emails partent de contact@lumenjuris.fr, boîte professionnelle de
  Lumen Juris (Google Workspace), signés au nom de Lumen Juris.
- Le compte qui exécute l'automatisation et la boîte expéditrice sont
  distincts : l'automatisation tourne sur le compte d'Édouard Lopro
  (edouardlopro@gmail.com), fondateur, et envoie depuis la boîte de
  l'entreprise. Aucun compte personnel de tiers n'est utilisé.

PÉRIMÈTRE
- Destinataires : uniquement les adresses institutionnelles publiques des
  bureaux des stages / relations entreprises d'écoles de commerce françaises.
  Jamais l'adresse personnelle d'un étudiant ou d'un particulier.
- Maximum 15 emails par exécution.
- Contenu : une offre de stage réelle. Pas de fausse urgence, pas d'affirmation
  invérifiable sur l'entreprise.

ACCÈS TECHNIQUE
- GMAIL_TOKEN_LUMEN = JSON base64 (client_id, client_secret, refresh_token)
  pour contact@lumenjuris.fr. Scopes : gmail.send + gmail.readonly +
  userinfo.email.
- Échanger le refresh_token contre un access_token sur
  https://oauth2.googleapis.com/token, puis POST sur
  https://gmail.googleapis.com/gmail/v1/users/me/messages/send, message MIME
  encodé en base64url dans le champ "raw". Aucune bibliothèque à installer.

DÉROULÉ
1. Contrôle préalable : appeler userinfo.email et vérifier que le token
   contrôle bien contact@lumenjuris.fr. Si l'adresse retournée est autre,
   s'arrêter et notifier.
2. Rechercher des écoles de commerce françaises : nom, ville, email du bureau
   des stages / relations entreprises.
3. Dédoublonnage obligatoire : interroger le libellé SENT via l'API Gmail.
   Ne jamais recontacter une adresse déjà contactée.
4. Envoyer un email personnalisé (nom de l'école et ville dans le corps, pas de
   texte générique) demandant si un étudiant serait intéressé par ce stage.
   Inclure un lien ou une mention permettant de se désinscrire / de ne plus
   être recontacté.
5. Mettre à jour ecoles.csv (École, Ville, Email, Statut, Date de contact),
   committer et pusher sur la branche de travail — le conteneur est détruit en
   fin de session.
6. Notifier en fin d'exécution : emails envoyés, écoles contactées, doublons
   évités, erreurs rencontrées.

S'ARRÊTER ET NOTIFIER SANS RIEN ENVOYER SI
- 401 / invalid_grant (token expiré).
- userinfo.email ne retourne pas contact@lumenjuris.fr.
- Le périmètre ci-dessus ne couvre pas ce qui est demandé (autres destinataires,
  autre contenu que cette offre de stage).
- Incohérence entre ce prompt et l'état réel du dépôt ou du compte.

---

## Ce qui a changé par rapport à la version précédente

1. **Expéditeur** — `contact@lumenjuris.fr` au lieu du Gmail personnel de
   Geoffrey. C'est le changement de fond : plus de compte personnel d'un tiers
   dans la boucle, donc plus de question de consentement à recouper.
2. **Scopes réduits** — `gmail.send` + `gmail.readonly` (lecture du libellé SENT
   pour le dédoublonnage) au lieu de `gmail.modify`, qui autorisait aussi la
   modification et la suppression de messages. Le dédoublonnage n'en a pas
   besoin.
3. **Contrôle d'identité en étape 1** — l'automatisation vérifie elle-même
   depuis quelle boîte elle s'apprête à écrire, au lieu de le supposer.
4. **Ligne « exécuter sans confirmation préalable » retirée.** Elle produisait
   l'effet inverse de celui recherché : c'est exactement la phrase qu'écrirait
   quelqu'un qui anticipe une objection fondée. Le périmètre et les conditions
   d'arrêt suffisent à cadrer l'exécution.
5. **Mention de désinscription** ajoutée au contenu des emails — usage courant
   en prospection, et attendu côté RGPD pour une sollicitation non sollicitée.

## Prérequis avant première exécution

- [ ] Créer `contact@lumenjuris.fr` sur Google Workspace.
- [ ] Configurer SPF, DKIM et DMARC sur le domaine `lumenjuris.fr` — sans quoi
      la prospection en volume part en spam.
- [ ] Créer un projet OAuth, autoriser les scopes ci-dessus, générer le
      refresh_token, publier l'app (en mode Testing les refresh tokens expirent
      sous ~7 jours).
- [ ] Exposer `GMAIL_TOKEN_LUMEN` dans l'environnement de la tâche planifiée.
- [ ] Retirer de l'environnement les secrets devenus inutiles :
      `GMAIL_TOKEN_GEOFFREY`, `SMTP_PASS_GEOFFREY`, `SMTP_PASS_LUMEN`.
      Ils y sont aujourd'hui en clair.
