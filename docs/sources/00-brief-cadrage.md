# Brief de cadrage — plugin `holmesMcp` (Holmes MCP)

> Document autonome destiné à être ingéré par Claude Code en mode planification, dans un repo GitHub vide nouvellement créé. Ce brief consolide l'intégralité des décisions issues d'une session d'idéation (D1.1 à D15.10) et liste les éléments structurants à transférer depuis la session.
>
> **Note méthodologique** : ce brief est la **source figée** d'entrée de la session de planning Claude Code. Il ne devient pas le `PLANNING.md` du repo — celui-ci sera **produit en sortie** de la première session par Claude Code, à partir de ce brief. Le brief reste tel quel dans `docs/sources/00-brief-cadrage.md` comme référence d'autorité ; le `PLANNING.md` vivant et opérationnel se trouve dans `docs/PLANNING.md`. Toute évolution ou amendement des décisions tranchées dans ce brief fait l'objet d'une ADR explicite dans `docs/decisions/`, pas d'une modification du brief lui-même.

---

## Préambule

`holmesMcp` (nom human : **Holmes MCP**) est un plugin Jeedom natif open source sous licence AGPL-3.0 qui expose la box Jeedom comme serveur MCP (Model Context Protocol) à n'importe quel client compatible (Claude Desktop, Cursor, MCP Inspector, n8n, autres). Il s'inscrit dans la **sphère jeedom-audit** : projet séparé de `jeedom-skills` (la skill Claude Code mère), mais avec un couplage acté à terme — la skill jeedom-audit basculera dans une version future en consommatrice exclusive de Holmes MCP pour ses accès aux données Jeedom (D5.8).

**Identité produit** : *Holmes observe, déduit, raconte — sans jamais toucher à la scène, sans jamais exposer les secrets de votre maison.* Lecture seule en V1, sanitisation forte des credentials, garantie technique read-only au niveau base de données. L'écriture (exécuter scénario, modifier dataStore, etc.) est candidate roadmap V2+, jamais via SQL direct.

**Cible utilisateur** : Jeedomistes éclairés équipés d'un client MCP (Claude Desktop, Cursor…) qui veulent interagir avec leur installation domotique en langage naturel, **sans setup technique côté client** (pas de Python, pas de SSH — juste une URL et un token à coller dans leur client MCP).

**Profil technique du PO** : utilisateur Jeedom éclairé, **non-développeur**. Ne maîtrise ni Python, ni PHP, ni les structures internes des plugins Jeedom. Le plugin est développé par Claude Code à partir des arbitrages PO et de cette idéation, en binôme — pas en codant directement. Le PO dispose d'une box Debian 12 Bookworm x86_64 sous Proxmox et d'un alias SSH `Jeedom` opérationnel utilisé pour la skill jeedom-audit, dont Claude Code héritera (D11.7, D11.8).

**Cible OS V1** : Debian 12 Bookworm x86_64 + Jeedom 4.5+, ferme. Bullseye, ARM/Pi, autres : best-effort non testé V1.

**ADRs source** :
- ADR-0019 (superseded) — Architecture MCP : options A/B/C
- ADR-0020 (accepted) — `jeedom-mcp` projet séparé, plugin Jeedom natif (Option C)
- ADR-0006 (amendé) — Lecture seule absolue *perpétuelle* pour `jeedom-audit` (le présent projet n'est pas concerné par cette perpétuité — il est lecture seule en V1, écriture candidate V2+)

---

### Posture de conception : clean room

Holmes MCP est conçu **en clean room**, à partir uniquement :
- des scripts pré-existants de `jeedom-audit` (écrits par le PO et Claude Code à partir des connaissances Jeedom du PO)
- de la documentation Jeedom officielle (publique, neutre)
- de la spécification MCP officielle d'Anthropic (publique, neutre)
- des choix d'architecture et de produit pris dans la session d'idéation amont, fondés sur le contexte propre du projet

Toute similitude avec d'autres plugins Jeedom existants — qu'ils soient open source ou propriétaires, présents ou futurs — découle de la **convergence naturelle** qu'imposent (a) la spécification MCP elle-même, (b) le schéma de la base de données Jeedom, (c) l'API JSON-RPC de Jeedom, et (d) les conventions de développement plugin Jeedom documentées par le core. Cette convergence n'est pas une réutilisation de code.

Cette posture protège le projet de toute accusation de plagiat, et garantit l'indépendance des choix de design. Elle vaut pour toute la durée du projet : Claude Code n'audite pas le code des autres plugins MCP Jeedom, ne s'inspire pas de leurs schémas de tools, ne lit pas leurs threads techniques au-delà de ce qui est strictement nécessaire pour vérifier la disponibilité d'un identifiant ou détecter une collision de port.

---

## 0. Modèle opérationnel Product Owner / Claude Code

**À lire en premier par Claude Code.** Ce brief décrit ce qui doit être construit, pas qui le construit. Cette section pose le binôme.

### 0.1 Répartition des rôles

| Rôle | Qui | Responsabilités |
|---|---|---|
| **Product Owner (PO)** | L'utilisateur humain | Décide, oriente, arbitre. Fournit les matières que Claude Code ne peut pas produire seul (captures d'écran UI Jeedom, validation Claude Desktop sur sa machine, sanity check sanitisation, soumission market, communication forum). Ne tape pas de code, ne rédige pas de doc, n'exécute pas de scripts complexes. |
| **Implémenteur** | Claude Code | Code, rédige, propose, pose des questions structurées quand un arbitrage est nécessaire. Produit tous les artefacts du repo (ADRs, guides, doc utilisateur, références, scripts, tests). Avec accès SSH à la box du PO (D11.7), exécute aussi : tests live, déploiements, smoke tests, récupération de fixtures réelles, debug. Demande explicitement les matières physiques au PO. |

### 0.2 Conséquences pratiques pour Claude Code

**(a) Pas d'attente que le PO rédige.** Tout texte (ADR, guide, doc utilisateur, README, code, tests) est **rédigé par Claude Code**. Le PO valide ou demande retouche.

**(b) Pose des questions structurées, pas ouvertes.** Quand un arbitrage est nécessaire, présenter au PO **2 à 4 options claires** avec leurs trade-offs plutôt qu'une question abstraite. Indiquer une recommandation par défaut quand possible. Le PO peut accepter, choisir une autre option, ou demander à débattre.

**(c) Préférer "valider un draft" à "produire ex nihilo via questions".** Quand il s'agit de rédiger une section ou un fichier, **Claude Code produit un draft** et le PO le critique.

**(d) Auto-validation des choix triviaux.** Conventions de nommage internes, organisation de fichiers internes (au-delà de ce qui est tranché ici), choix de variables, formulations mineures dans les drafts : Claude Code décide seul et avance. Pas de gaspillage de cycles de validation sur des détails.

**(e) Demande explicite des matières physiques.** Goulets d'étranglement physiques où le PO est obligatoire :
1. Captures d'écran UI Jeedom (page de config plugin, état daemon, fiche market) — voir D12.6
2. Validation finale Claude Desktop sur la machine PO avant V1.0.0 (D8.3 critère 4)
3. Sanity check sanitisation finale sur installation réelle (D15.6)
4. Soumission market Jeedom (compte développeur PO)
5. Communication forum Jeedom (identité PO)
6. **Snapshots Proxmox** du conteneur Jeedom avant chaque session SSH significative impliquant install/désinstall plugin ou tests live nombreux (~30s par snapshot, sécurité opérationnelle)

Demandes au PO : **explicites, timées, groupées** ("À l'étape J7, j'ai besoin de 3 captures + validation Claude Desktop + sanity check sanitisation").

**(f) Sessions courtes orientées avancement.** Préférer plusieurs sessions ciblées avec validation PO entre les deux à une session marathon qui produit beaucoup sans validation intermédiaire.

### 0.3 Discipline de continuité entre sessions

Le PO ne mémorise pas les détails techniques entre sessions. C'est l'**axe documentaire** (continuité Claude Code) qui assure la persistance — `docs/state/PROJECT_STATE.md` et `docs/sessions/*.md` mis à jour à chaque session significative.

**Routine de début de session Claude Code** :
1. Lire `docs/README.md`
2. Lire `docs/state/PROJECT_STATE.md`
3. Lire les ADRs récentes
4. Lire la dernière entrée `docs/sessions/`
5. Annoncer au PO l'état + objectifs de la session

**Routine de fin de session significative** :
1. Mise à jour `docs/state/PROJECT_STATE.md`
2. Nouvelle entrée `docs/sessions/`
3. ADR(s) si décisions non triviales prises
4. Commit + tag pre-release si jalon atteint

### 0.4 Cadre d'usage de l'accès SSH PO

Claude Code dispose d'un alias SSH `Jeedom` opérationnel sur sa machine de dev (déjà en place pour jeedom-audit).

**Identité du user SSH** : Claude Code se connecte avec l'utilisateur **`jeedom`** du système (user standard sous lequel tournent le daemon Apache/Jeedom et donc le futur daemon Holmes MCP). Choix volontaire du PO pour que Claude Code reproduise fidèlement le contexte d'exécution réel du plugin (mêmes droits fichiers, même environnement, mêmes contraintes que le daemon en production).

**Conséquence de ce choix** : la discipline de prompt est le **filet de sécurité principal** (pas de couche OS restrictive complémentaire). Les garde-fous suivants sont **non négociables** :

**Conditions générales d'usage** :
- Actions limitées au plugin Holmes MCP (lecture, install/test, démarrage/arrêt daemon plugin)
- **Aucune modification non autorisée** de la config Jeedom, des autres plugins, du système hors plugin
- Logs des actions SSH dans `docs/sessions/` pour traçabilité PO
- En cas de doute, demande PO avant action

**Blacklist explicite de classes de commandes interdites sans validation PO préalable explicite** :
- `rm -rf`, `rm -r` sur tout chemin hors `/tmp/` ou hors workspace de dev Holmes MCP
- `DROP DATABASE`, `DROP TABLE`, `DROP USER`, `TRUNCATE`, `DELETE FROM`, `UPDATE`, `INSERT` (toute requête modifiante MySQL)
- Modifications de fichiers dans `/etc/`, `/usr/`, `/var/log/` (hors logs Jeedom du plugin Holmes MCP)
- `chmod`/`chown` sur fichiers ou dossiers non liés au plugin Holmes MCP
- `apt-get install/remove/purge`, `pip install` hors venv Holmes MCP
- `systemctl stop/disable/mask` sur services autres que ceux du plugin Holmes MCP
- Toute commande `sudo` (le user `jeedom` ne devrait pas en avoir besoin pour le plugin)
- Toute manipulation de `~/.ssh/`, `/etc/shadow`, `/etc/passwd`, fichiers de creds Jeedom (`common.config.php` reste accessible en lecture pour D4bis.2)
- Toute commande qui pourrait déclencher un redémarrage système ou la coupure du serveur web

Si Claude Code juge nécessaire d'exécuter l'une de ces commandes, **demande explicite au PO en chat avec justification + commande exacte**. Le PO valide ou refuse. Pas d'exécution préemptive "je supprime juste pour nettoyer", pas de `rm -rf` "défensif".

**Reco opérationnelle PO — snapshot Proxmox avant session SSH significative** : la box Jeedom du PO tourne sous Proxmox. Avant chaque session impliquant install/désinstall plugin ou tests live nombreux, le PO **prend un snapshot du conteneur Jeedom** (~30s) pour pouvoir rollback en 1 commande si quelque chose tourne mal. Ce n'est pas dans la responsabilité de Claude Code (pas d'accès Proxmox), c'est un **goulet PO** listé en section 0.2.e ci-dessous. Claude Code annonce en début de session "je vais avoir besoin d'accès SSH avec install/désinstall plugin, snapshot recommandé" et attend confirmation PO avant action.

### 0.5 Isolation des credentials et de la configuration d'accès

**Aucun credential, alias SSH, IP, hostname, user MySQL, port, mot de passe, token, apikey, chemin absolu PO-spécifique, ou identifiant lié à l'environnement PO ne doit apparaître dans le repo Holmes MCP.** Stockage exclusif sur la devbox Claude Code.

**Garde-fous techniques** : `.gitignore` strict, pre-commit + pre-push hooks de scan automatique, review systématique des PR vers `main` avec checklist credentials, procédure de réponse rapide en cas de leak (rewrite history, force push, rotation immédiate, ADR d'incident).

**Documentation publique** : placeholders systématiques (`<your-jeedom-host>`, `<your-mysql-password>`, `<your-mcp-token>`).

**Logs de sessions Claude Code** : références neutres aux actions SSH, pas de commande brute incluant des éléments sensibles.

**Fixtures réelles MySQL** : workspace local Claude Code uniquement (hors repo). Fixtures synthétiques uniquement dans le repo.

---

## 1. Primitives MCP exposées

> **Concept (encadré factuel)** — MCP (Model Context Protocol, Anthropic) expose 3 primitives à un client LLM compatible : **tools** (verbes appelés par le LLM), **resources** (URIs attachables par l'utilisateur), **prompts** (slash commands). Découverte via `tools/list`, `resources/list`, `prompts/list`. Transports : stdio (local) ou Streamable HTTP (réseau).

### D1.1 — Primitives V1
🟡 **Tools ✅ inclus** (cœur du plugin). **Resources** : 5 minimales basées sur tools (D6.2). **Prompts ❌ exclus V1**, candidats roadmap V1.x sur retour communauté.

Rationale : tools couvrent l'usage essentiel ; resources V1 minimales = effort marginal faible (wrapping de tools existants) ; prompts coûteux en évals et au support client variable, à introduire après observation des usages réels.

### D1.2 — Version de la spec MCP cible
🔵 **Délégué Claude Code J0** — Cibler la dernière version stable au moment du J0 effectif.

**Critères pour Claude Code** :
1. Dernière version stable de la spec MCP au J0 effectif
2. Compatibilité avec le SDK MCP Python officiel retenu (D2.1, D9.1)
3. Documenter en ADR : numéro de version + politique de support (typiquement N et N-1, alignée jeedom-skills)
4. Mention claire dans le README V1 de la version MCP supportée pour que les utilisateurs puissent vérifier la compatibilité de leur client

---

## 2. Architecture du plugin

> **Concept (encadré factuel)** — Un plugin Jeedom standard est l'assemblage d'un manifeste `info.json`, d'une classe PHP héritant d'`eqLogic`, de vues `desktop/`, et optionnellement d'un *daemon* (processus permanent, souvent Python ou Node.js, lancé/arrêté par les hooks `deamon_*` côté PHP — graphie officielle avec faute, conservée par le core). Le pattern "plugin PHP minimaliste + daemon Python" est documenté par Jeedom (`doc.jeedom.com/fr_FR/dev/daemon_plugin`) et utilisé par jMQTT, Mobile, et d'autres plugins majeurs.

### D2.1 — Stack du daemon MCP
🟡 **Daemon Python 3.11+** lancé par un plugin PHP minimaliste qui sert d'enveloppe market.

Rationale : SDK MCP Python officiel d'Anthropic (premier servi sur les évolutions spec) ; réutilisation forte des scripts existants (D7.1) ; diagnostic le plus accessible pour PO non-dev ; précédents Jeedom solides (jMQTT, Mobile) ; pattern documenté officiellement par Jeedom.

### D2.2 — Rôle exact du PHP plugin
🟡 PHP fait **uniquement** :
- Manifeste `info.json` (`hasOwnDeamon: true`, `hasDependency: true`, `maxDependancyInstallTime`)
- Page de config UI (URL/port d'écoute MCP, tokens par utilisateur, niveau de log)
- Méthodes obligatoires : `deamon_info()`, `deamon_start()`, `deamon_stop()`, `dependancy_info()`, `dependancy_install()` (le cas échéant)
- Endpoint callback `core/php/jeeholmesMcp.php` pour recevoir les messages remontants du daemon (mécanisme `jeedom_com.send_change_immediate()` côté Python)
- Socket TCP côté PHP pour envoyer les commandes admin internes au daemon (optionnel V1, pattern Mips)

PHP **ne touche jamais au protocole MCP**. Tout MCP vit entièrement dans le daemon Python.

### D2.3 — POC J0 "faisabilité daemon Python sur Bookworm"
🟣 **POC requis sur la box du PO avant figeage du PLANNING.**

Cinq points à valider :
1. Installation du SDK MCP Python officiel dans un **venv géré via `packages.json`** (méthode moderne Jeedom 4.4.9+) — vérifier que `system::getCmdPython3(__CLASS__)` retourne le Python du venv après installation des deps
2. Daemon Python "hello world MCP" lancé par `deamon_start()` PHP, écriture du pidfile, `deamon_info()` retournant l'état correct
3. Affichage état daemon vert/rouge dans le cadre "Démon" UI plugin standard Jeedom
4. Réponse à `tools/list` MCP : un client MCP externe (MCP Inspector) qui se connecte au port HTTP MCP exposé reçoit la liste de tools déclarés (au moins un tool fictif `hello`)
5. **Connexion réelle depuis Claude Desktop installé sur la machine du PO** vers l'URL HTTP du daemon en LAN (`http://<ip-jeedom>:<port>/mcp` + Bearer token). Le client MCP Claude Desktop est réputé pointilleux sur les connexions HTTP non-TLS, même en LAN privé. Validation indispensable avant figeage de la stratégie transport.

**Goulet PO physique sur le 5e point** : Claude Code n'a pas accès à la machine PO et à son installation Claude Desktop. Le PO conduit ce test en partage écran/log avec Claude Code, ou rapporte le résultat avec captures à l'appui. Listé en section 0.2.e (matières physiques requises du PO).

**Critère de succès** : 5 points validés, plugin "shell" installable via mécanisme Jeedom standard, démarrage/arrêt/monitoring corrects, réponse MCP externe **et** connexion Claude Desktop opérationnelle en HTTP LAN sur la machine PO.

**Critère d'échec** : impossibilité sur l'un des 5 points malgré 2-3 jours de recherche (~3-4 sessions Claude Code).

**Plan B si échec** :
- Si problème SDK Python sur Bookworm via venv → escalade PHP (Option B de l'ADR-0019), assumer dette SDK communautaire
- Si problème intégration daemon Jeedom → garder Python mais lancer via systemd externe (perte UX market)
- Si problème spécifique au pattern packages.json/venv → fallback méthode `dependancy_install()` + script shell adapté Bookworm
- **Si problème connexion Claude Desktop HTTP non-TLS en LAN (point 5)** → activation du **plan B HTTPS self-signed** : génération automatique d'un certificat self-signed à l'install du plugin (commande `openssl` côté PHP via `holmesMcp_install()`), exposition du daemon Python en HTTPS sur le port configuré, instructions documentées pour ajouter le certif aux trust stores du client (Claude Desktop, Cursor, etc.). Coût estimé : +1 à 2 jours d'implémentation, mais évite un blocage utilisateur majeur en V1. ADR à rédiger documentant le passage HTTP → HTTPS self-signed.
- ADR de l'arbitrage retenu

### D2.4 — Matrice OS supportée + méthode dépendances
🟡 + 🔵 (détails délégués J0)

**Cible V1 ferme** : Debian 12 Bookworm x86_64 + Jeedom 4.5+.

**Best-effort non testé V1** : Debian 11 Bullseye, ARM/Raspberry Pi, autres distros, NAS Linux. Mention explicite dans le README et `info.json.os` (`{"min": 12, "max": 12.99}` ou similaire à arbitrer).

**Méthode de gestion des deps Python** : `plugin_info/packages.json` (méthode moderne Jeedom 4.2+) avec `apt` + `pip3`, **+** utilisation impérative de `system::getCmdPython3(__CLASS__)` côté PHP pour respecter le venv géré par le core Jeedom 4.4.9+.

**Détails délégués Claude Code J0 (🔵)** :
- Évaluation de `dependance.lib` (Mips) en complément du mécanisme natif → critère : adopter uniquement si bénéfice clair sans complexifier le diagnostic
- Liste exacte des paquets `apt` + modules `pip3` requis (dépend du SDK MCP Python ciblé en D1.2 et des bibliothèques D9.1)
- Politique de version Python min (3.10 vs 3.11) → la plus basse compatible avec le SDK MCP Python officiel cible

---

## 3. Transport MCP

> **Concept (encadré factuel)** — La spec MCP définit deux transports : **stdio** (sous-processus, local uniquement, exclu pour un plugin Jeedom accessible distance) et **Streamable HTTP** (forme moderne de la spec 2025-03-26+, anciennement HTTP+SSE déprécié). Streamable HTTP = un endpoint HTTP unique qui sert des réponses simples ou streamées selon le besoin, avec gestion de session via header `Mcp-Session-Id`.

### D3.1 — Transport MCP exposé par le daemon
🟡 **Streamable HTTP** (forme moderne de la spec, 2025-03-26+).

Rationale : seul transport viable pour un serveur sur la box accédé depuis un client distant ; aligné avec D1.2 (dernière version stable de la spec MCP cible).

### D3.2 — Binding et port d'écoute du daemon
🟡 (principe) + 🔵 (détail port et path)

**Principe** : écoute par défaut sur `0.0.0.0:<port-configurable>/mcp`, port configurable depuis l'UI plugin Jeedom.

**Délégué Claude Code J0 (🔵)** :
1. Choix du port par défaut → critère : port "haut" (>8000) **non utilisé par les plugins Jeedom majeurs** (vérifier au minimum : MQTT Manager, jMQTT, MP_Server, Mobile, Z-Wave JS UI, Zigbee2MQTT, et tout autre plugin observé sur la box du PO via `netstat`). Documenter en ADR.
2. Path de l'endpoint MCP (`/mcp` vs autre) → critère : aligner sur la convention par défaut du SDK MCP Python officiel cible.

### D3.3 — Communication de l'URL au client final
🟡 La page de configuration du plugin Jeedom **affiche explicitement l'URL complète à coller dans le client MCP** (forme typique : `http://<ip-jeedom>:<port>/mcp` + token Bearer — D4). L'IP est détectée côté PHP via les helpers Jeedom (`network::getNetworkAccess('internal', 'http:127.0.0.1:port:comp')` — pattern de la doc daemon officielle).

Rationale : zéro ambiguïté pour l'utilisateur, page de config = source de vérité, aligné avec contrainte non négociable "pas de setup client".


---

## 4. Authentification MCP externe

> **Concept (encadré factuel)** — Trois canaux d'auth coexistent dans le système : (1) **MCP externe** (client MCP → daemon Python, sujet de cette dimension), (2) **interne PHP↔daemon** (mécanisme natif Jeedom via `jeedom::getApiKey(__CLASS__)`, hors scope), (3) **daemon → API JSON-RPC Jeedom localhost** (apikey JSON-RPC globale Jeedom, sujet 4bis). Cette dimension traite uniquement le canal externe. Standard de fait MCP : header `Authorization: Bearer <token>` sur Streamable HTTP.

### D4.1 — Stratégie d'auth MCP externe
🟡 **Token MCP dédié, transmis en header `Authorization: Bearer <token>`.**

Rationale : standard de fait MCP, séparation des scopes propre, indépendant des apikeys Jeedom existantes.

### D4.2 — Génération et gestion des tokens
🟡 **Un token par utilisateur Jeedom**, géré via le mécanisme natif des options utilisateur Jeedom (pattern `specialAttributes.user` de la doc `info.json` officielle).

- À l'installation du plugin : génération automatique d'un token (UUID 32+ caractères, source aléatoire cryptographique) pour chaque utilisateur Jeedom existant
- À la création d'un nouvel utilisateur Jeedom : génération automatique de son token (hook PHP, mécanisme exact à confirmer J0 par lecture de plugins existants)
- **Page de config plugin** : tableau "Utilisateurs Jeedom et leurs tokens MCP" avec, pour chacun, nom utilisateur, son token, bouton "Régénérer" individuel, bouton "Révoquer" individuel
- Stockage via `User->setOption()` / `User->getOption()` natif Jeedom

### D4.3 — HTTPS / TLS
🟡 **HTTP par défaut côté plugin V1.**

Le README documente explicitement : HTTP est acceptable en LAN privé ; toute exposition hors LAN nécessite un reverse proxy HTTPS externe (nginx, traefik, Caddy, Cloudflare Tunnel) — non géré par le plugin.

Rationale : intégrer HTTPS dans le daemon V1 = gestion certificats (Let's Encrypt, self-signed, renouvellement) → complexité hors proportion avec V1. La voie reverse proxy est standard et bien documentée.

### D4.4 — Scopes du token
🟡 **Token unique avec un seul niveau d'autorisation V1**, dont le périmètre dépend de D5.1 (lecture seule en V1, écriture candidate V2+). Tous les utilisateurs avec un token MCP V1 ont les mêmes droits MCP. Différenciation des permissions par rôle Jeedom (admin/user) = roadmap V1.x.

### D4.5 — Multi-utilisateur / multi-tokens
🟡 **V1 : un token par utilisateur Jeedom.** Aligné sur le système d'identité natif Jeedom. Multi-tokens par utilisateur (un par client/appareil) = candidate roadmap V1.x si demande communautaire.

### D4.6 — Comportement face à requête non auth
🟡 Le daemon MCP rejette toute requête sans token valide avec un code HTTP 401 + message explicite côté logs. **Pas de fallback "lecture limitée sans auth".**

### D4.7 — Identification dans les logs daemon
🟡 Le daemon **logue chaque requête MCP entrante avec l'identité de l'utilisateur Jeedom résolue à partir du token**. Format : voir D14.1 (schéma JSON Lines avec champ `user`). Permet d'attribuer chaque requête à une identité Jeedom dans les logs (cf. D15).

---

## 4bis. Accès aux données Jeedom (MySQL, logs, API)

> **Concept (encadré factuel)** — Le daemon Python a besoin de trois canaux d'accès distincts aux données Jeedom : MySQL (structure), fichiers de log (diagnostic), API JSON-RPC (runtime). Dans `jeedom-audit`, ces trois canaux passent par SSH ou HTTP depuis l'extérieur. Dans Holmes MCP, le daemon est *sur* la box → accès local direct, avec choix d'architecture spécifiques à acter.

### D4bis.1 — Stratégie d'accès MySQL
🟡 (principe) + 🔵 (choix driver)

**Principe** : driver MySQL Python direct sur localhost:3306 + **user MySQL dédié read-only `jeedom_mcp_ro`** créé automatiquement à l'install du plugin.

**Délégué Claude Code J0 (🔵)** : choix entre PyMySQL et mysql-connector-python.

**Critères Claude Code J0 pour le driver** :
1. Pure Python (pas de deps C compilées) si possible
2. Maintenance active (commits dans les 12 derniers mois)
3. Support Python 3.11+ confirmé
4. Compatible MySQL 5.7 + MariaDB 10.x (versions Jeedom)
5. **Reco par défaut : PyMySQL** sauf raison forte de choisir autrement

### D4bis.2 — Création/suppression du user MySQL aux hooks install/remove
🟡 + 🔵 (détail mécanisme)

- À `holmesMcp_install()` : création du user `jeedom_mcp_ro` avec password aléatoire généré, `GRANT SELECT ON jeedom.* TO 'jeedom_mcp_ro'@'localhost'`
- Password stocké via `config::save('mysql_ro_password', ..., 'holmesMcp')`
- Au démarrage du daemon : password passé en CLI arg (pattern `_apikey` du template Jeedom)
- À `holmesMcp_remove()` : drop user et révocation des privilèges

**Délégué Claude Code J0 (🔵)** : mécanisme exact d'obtention des creds Jeedom et de création du user.

**Critères Claude Code J0** :
1. Lire `core/config/common.config.php` côté PHP pour récupérer les creds Jeedom (lecture seule de la config)
2. Tester si la création de user fonctionne (le user Jeedom standard a-t-il `CREATE USER` privilege ?)
3. Si pas de privilege CREATE USER → message clair à l'utilisateur (rare mais existe selon types d'install)
4. Documenter en ADR le mécanisme retenu

### D4bis.3 — Stratégie d'accès aux logs Jeedom
🟡 **Lecture directe des fichiers de log Jeedom** par le daemon Python, avec résolution dynamique du chemin au démarrage (réutiliser le pattern `_LOG_DIRS` de `logs_query.py` jeedom-audit). Le daemon tourne sous l'user Jeedom/Apache (`www-data` typiquement) → lecture native disponible.

### D4bis.4 — Stratégie d'accès à l'API JSON-RPC Jeedom (runtime)
🟡 **Appel HTTP localhost** à `http://127.0.0.1/core/api/jeeApi.php` avec l'apikey JSON-RPC Jeedom globale, récupérée côté PHP au démarrage et passée au daemon en CLI arg. Pattern réutilisé de `api_call.py` jeedom-audit (mêmes méthodes, IP=localhost).

### D4bis.5 — Politique de méthodes API autorisées
🟡 (clôturée après D5.1)

**V1 (lecture seule, D5.1) : blacklist hard-codée** des méthodes JSON-RPC modifiantes côté daemon. Liste dérivée de `api_call.py` jeedom-audit : `cmd::execCmd`, `scenario::changeState`, `datastore::save`, `interact::tryToReply`, et tout pattern dont le nom suggère une modification.

**V2+ si scope inclut écriture** : whitelist explicite des méthodes autorisées (pas un retrait progressif de la blacklist). Approche positive plus saine.

Liste auditable dans les deux cas, modification = ADR.

### D4bis.6 — Routage par opération
🟡 Tableau de routage hard-codé dans le daemon (équivalent simplifié du `router.py` jeedom-audit, pas de `preferred_mode` car local uniquement) :

| Opération | Canal |
|---|---|
| Audit structurel (jointures, scénarios, équipements, commandes, plugins) | MySQL |
| État runtime (`lastLaunch`, `state`, `currentValue`) | API JSON-RPC |
| History récente | API JSON-RPC |
| History archivée | MySQL (`historyArch`) |
| Logs | Fichier local |
| Actions modifiantes (V2+) | API JSON-RPC uniquement, jamais SQL |

### D4bis.7 — Garantie technique de read-only DB
🟡 **Le user MySQL `jeedom_mcp_ro` n'a que `SELECT`** à perpétuité, quelle que soit la version du plugin. Aucun INSERT/UPDATE/DELETE possible côté daemon, même en cas de bug ou prompt injection.

**En V2+ si écriture autorisée**, elle passera **exclusivement par l'API JSON-RPC** (jamais en SQL direct). Pas de drift identitaire `holmesMcp` vers `jeedom-audit` : la lecture seule de Holmes MCP V1 est un choix de scope V1, pas un engagement perpétuel — l'engagement perpétuel concerne uniquement le canal SQL.

---

## 5. Tools à exposer + périmètre fonctionnel V1

### D5.1 — Périmètre fonctionnel V1 (décision pivot)
🟡 **Lecture + assistance à la conception en V1. Pas d'écriture directe en V1.** Capacités modifiantes (exécuter scénario, écrire dataStore, modifier configuration légère) en candidates roadmap V2+, à ré-arbitrer après retours communauté V1.

Rationale :
1. Le coût des garde-fous d'écriture V1 (scopes, dry-run, journal, whitelist, confirmations) est élevé pour un binôme PO non-dev / Claude Code
2. Asymétrie de risque : V2 ajoute l'écriture sans rien casser ; V1 écriture qui rate (incident, fuite, modification silencieuse) casse la confiance et est difficile à reconstruire
3. L'usage "lecture + assistance" V1 est un terrain d'apprentissage pour comprendre ce que les utilisateurs *demandent vraiment* de modifier — oriente la liste exacte des actions à exposer en V2+

### D5.2 — Stratégie d'assistance à la conception V1
🟡 **Émergente côté LLM, soutenue par tools de lecture riches.** Pas de tool serveur "design" / "propose_scenario" en V1.

Concrètement : le LLM (Claude Desktop, Cursor, etc.) lit l'install via les tools de lecture, comprend le contexte, et **rédige lui-même** la proposition de scénario / virtuel / objet en pseudo-code Jeedom + pas-à-pas UI. Le plugin n'a pas de tool "magique" qui produit du pseudo-code — c'est une capacité émergente du LLM.

**Implication** : les tools de lecture doivent retourner des structures riches et lisibles (pas du SQL brut), avec les conventions Jeedom (Types Génériques, `#[Objet][Équipement][Commande]#`, `logicalId`, etc.) bien représentées. Les schémas et descriptions des tools rappellent les conventions Jeedom au LLM.

Tool serveur "design" candidat roadmap V1.x si retours utilisateurs montrent un besoin de cadrage plus fort.

### D5.3 — Liste des tools V1
🟢 (PO décide la liste finale, raffinable J1 par Claude Code selon D5.8)

**25 tools en 6 familles** :

**Famille 1 — Découverte d'install**
1. `get_install_overview` — Snapshot général (version Jeedom, nb équipements/scénarios/plugins, état général)
2. `list_objects` — Hiérarchie des objets Jeedom (= "pièces")
3. `list_plugins` — Plugins installés avec version et état
4. `get_config` — Config Jeedom de la table `config` (filtrable par namespace `core`/`<pluginID>`/`*` et regex de clé). Sanitisation runtime des valeurs sensibles, noms de clés toujours visibles. Voir D5.6.bis.

**Famille 2 — Équipements et commandes**
5. `list_equipments` — Liste filtrable (objet, plugin, état actif)
6. `find_equipments_advanced` — Filtres avancés (plugin, type générique, historisation, état actif, dernier seen)
7. `get_equipment` — Détail complet (commandes, configuration sanitisée, état)
8. `find_equipment_by_name` — Recherche fuzzy par nom
9. `list_commands` — Commandes d'un équipement (types, sous-types, type générique)
10. `find_commands_advanced` — Filtres avancés (type info/action, sous-type, type générique, historisée, valeur courante)
11. `get_command_history` — Historique d'une commande info (live + archivée)

**Famille 3 — Scénarios**
12. `list_scenarios` — Liste filtrable, état d'activation
13. `find_scenarios_advanced` — Filtres avancés (actif, dernière exécution, mode, contient telle commande, mots-clés)
14. `get_scenario` — Détail complet (déclencheurs, structure, dernier lancement, log dernier run)
15. `get_scenario_structure` — Arbre brut (noeuds, parents, types `if`/`then`/`else`/`for`/`action`/`code`, expressions, options) — réutilise `scenario_tree_walker.py`. Format machine-friendly.
16. `describe_scenario` — Description fidèle au rendu UI Jeedom (Si/Alors/Sinon, Pour, conditions, actions, sous-scénarios, modes), avec résolution `#[O][E][C]#` systématique. Format lisible, utile à l'audit ET à la rédaction de propositions de scénarios par le LLM.
17. `find_scenario_dependencies` — Quel scénario utilise quoi, qui est appelé par qui — réutilise `usage_graph.py`
18. `get_scenario_log` — Log du dernier run d'un scénario

**Famille 4 — Variables / dataStore**
19. `list_datastore_variables` — Variables persistantes globales et par scénario
20. `get_datastore_variable` — Valeur courante d'une variable

**Famille 5 — Logs et diagnostic**
21. `tail_log` — Tail d'un log Jeedom (core, plugin, scenarioLog/N) avec grep optionnel — réutilise `logs_query.py`
22. `list_log_files` — Liste des logs disponibles avec taille et dernière modification
23. `get_health_summary` — Daemons en panne, dépendances KO, messages système, cron en retard

**Famille 6 — Recherche transverse**
24. `search_text` — Recherche d'une chaîne dans noms d'équipements, commandes, scénarios, expressions de scénarios

**Power-user / Audit**
25. `query_sql` — SQL libre **restreint** : SELECT-only (parsing SQL côté daemon, rejet de tout autre statement), blacklist hard-codée des tables sensibles (`user`, `session`, `network`, regex `(?i).*creds?|credentials?|password|token.*`), LIMIT obligatoire, sanitisation runtime systématique des champs sensibles dans les résultats, description du tool inclut un mini SQL cookbook (mots réservés `trigger`/`update`/`repeat`, conventions Jeedom, liste des tables interdites). Cf. D5.6.

**Liste à raffiner J1 par Claude Code selon résultats de la matrice de couverture (D5.8). Ajouts/retraits soumis au PO pour validation.**

### D5.4 — Granularité des tools
🟡 **Tools spécifiques granulaires.** Pas de tool générique unique ; chaque tool a un schéma de paramètres clair, un schéma de retour stable, une description riche pour le LLM.

Rationale : les LLMs choisissent mieux entre 25 tools bien décrits qu'un tool qui fait tout. Préserve aussi la composabilité requise pour l'orchestration adaptative côté skill jeedom-audit (D5.8).

### D5.5 — Stabilité du contrat des tools (politique semver)
🟡 **Schémas in/out des tools V1 stables sur toute la branche V1.x.** Breaking changes uniquement entre versions majeures.

**Politique semver explicite** :
- `1.0.x` → patches (corrections, perfs, descriptions enrichies — schémas inchangés)
- `1.x.0` → minor (nouveaux tools, paramètres optionnels rétro-compatibles)
- `2.0.0` → major (breaking changes possibles, mais documentés et avec migration guide)

Cette politique sécurise aussi la skill jeedom-audit qui dépendra de Holmes MCP : elle pourra exiger `holmesMcp >= 1.0, < 2.0` dans ses prérequis.

### D5.6 — `query_sql` restreint dès V1
🟡 Tool `query_sql` **inclus dès V1**, avec restrictions fortes :

- **SELECT-only** (parsing SQL côté daemon, rejet de tout autre statement modifiant : INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE, RENAME, GRANT, REVOKE, etc.)
- **Blacklist hard-codée de tables interdites** (refus 400 + log warning + message LLM explicite) :
  - `user` (hash mots de passe Jeedom — pas de cas d'usage diagnostic légitime)
  - `session` (sessions actives, risque hijack)
  - `network` (config réseau)
  - Toute table dont le nom matche `(?i).*(creds?|credentials?|password|token).*` (regex défensive contre les tables custom de plugins tiers nommées explicitement sensibles)
- **`config` est autorisée** (cas d'usage diagnostic légitime : version Jeedom, config core, état général de la box) **avec filtrage runtime renforcé** : sanitisation systématique des lignes retournées dont la colonne `key` matche la regex sensible (`(?i)(api|password|pwd|token|secret|key|hash|credentials|auth|cert|private|bearer)`) — la colonne `value` est remplacée par `***FILTERED***`, le nom de la clé reste visible (transparence LLM-side). Voir aussi nouveau tool `get_config` ci-dessous (D5.6.bis), interface privilégiée pour ce cas d'usage.
- **LIMIT obligatoire** (refus si pas de LIMIT, pour éviter les requêtes monstres). LIMIT par défaut implicite si absent : `100` lignes pour `config`, `1000` lignes pour les autres tables
- **Sanitisation post-exécution** identique aux autres tools (D15) : regex sur noms de colonnes ET sur clés JSON dans les colonnes blob — quelle que soit la table (y compris tables propres aux plugins tiers)
- **Description du tool inclut un mini SQL cookbook** : mots réservés MySQL/MariaDB (`trigger`, `update`, `repeat` — backticks requis), conventions Jeedom (tables, jointures courantes, résolution `#[O][E][C]#` côté client), liste des tables interdites
- **Documentation séparée listant les requêtes SQL connues** (issue de `references/sql-cookbook.md` jeedom-audit)

**Conséquence du choix blacklist plutôt que whitelist** : `query_sql` peut interroger les tables propres aux plugins tiers (jMQTT, Aqara, etc. créent parfois leurs propres tables d'historique custom qui sont utiles aux workflows d'audit). La défense en profondeur ne repose pas sur le filtrage de tables mais sur (a) la sanitisation runtime des champs sensibles dans les résultats — quelle que soit la table — et (b) la blacklist défensive sur les tables explicitement nommées sensibles.

Rationale : avec la migration future de jeedom-audit consommatrice MCP (D5.8), retirer le canal SQL libre = perte de capacité majeure de la skill. `query_sql` restreint préserve la flexibilité, et les restrictions (SELECT-only + blacklist défensive + LIMIT + sanitisation runtime systématique) réduisent la surface d'attaque à un niveau acceptable. La blacklist plutôt que whitelist évite de se couper des tables custom de plugins tiers, légitimes pour le diagnostic.

### D5.6.bis — Tool dédié `get_config` (pour diagnostic standard sur la table `config`)
🟡 **Ajout d'un 25e tool** dans la famille 1 (Découverte d'install) — interface privilégiée pour interroger la table `config` dans 90 % des cas d'usage diagnostic standards.

**Tool `get_config`** :
- Retourne la config Jeedom (table `config`)
- Paramètre `namespace` optionnel (`core`, `<pluginID>`, ou `*` pour tous)
- Paramètre `key_pattern` optionnel (regex sur le nom de clé pour filtrage)
- Sanitisation runtime systématique : valeurs des clés sensibles (regex `(?i)(api|password|pwd|token|secret|key|hash|credentials|auth|cert|private|bearer)`) remplacées par `***FILTERED***`, **le nom de la clé reste visible** pour que le LLM sache qu'elle existe et puisse l'expliquer à l'utilisateur
- Description riche pour le LLM avec exemples de cas d'usage : "version Jeedom installée", "config cron", "état du market", "rétention de l'history"

Rationale : les LLM choisissent mieux entre un tool spécifique bien décrit (`get_config`) qu'un tool générique paramétré (`query_sql SELECT * FROM config`). `get_config` couvre 90 % des besoins, `query_sql` reste disponible pour les 10 % qui nécessitent des jointures ou filtres complexes.

**Liste D5.3 mise à jour** : 24 tools → **25 tools** (ajout de `get_config` en famille 1, après `list_plugins`). La numérotation interne et les autres décisions ne sont pas affectées.

### D5.7 — Tools de recherche avancée V1
🟡 Inclusion en V1 de `find_equipments_advanced`, `find_commands_advanced`, `find_scenarios_advanced` (tools 5, 9, 12 de la liste D5.3) avec filtres riches paramétrés (pas de SQL libre exposé).

Rationale : couvre 95 % des besoins de recherche complexe sans nécessiter de `query_sql`. Complète `query_sql` (D5.6) pour les cas les plus avancés.

### D5.8 — Couverture fonctionnelle des cas d'usage skill jeedom-audit
🔵 **Délégué Claude Code J1.**

Le périmètre V1 du MCP doit couvrir l'ensemble des **cas d'usage** actuellement servis par les scripts de jeedom-audit. Claude Code en J1 produit une **matrice de mapping** :

| Workflow skill (WF1-WF13 jeedom-audit) | Tools MCP impliqués | Couverture |
|---|---|---|
| WF1 (audit général) | `get_install_overview`, `find_equipments_advanced`, ... | ✅ |
| WF2 (diagnostic scénario qui ne déclenche pas) | `get_scenario`, `tail_log`, `get_scenario_structure`, ... | ✅ |
| ... | ... | ... |

Si un workflow n'est pas couvert → ADR justifiant le choix (différé V1.x ou tool ajouté).

**Critères pour Claude Code** :
1. Lire le SKILL.md de jeedom-audit + les références (`audit-templates.md`, `sql-cookbook.md`) pour identifier les WF1-WF13
2. Mapper chaque workflow aux tools MCP V1
3. Pour les workflows non couverts : ADR avec arbitrage (différer ou ajouter)
4. Livrable : `docs/skill-coverage-matrix.md`
5. Référencer les commits/tags précis de jeedom-audit auxquels la matrice se rapporte (pas de submodule)

---

## 6. Resources MCP

### D6.1 — Inclusion de resources V1
🟡 **Resources minimales V1** (5 resources) basées sur tools existants. Resources étendues (10+) en candidate roadmap V1.x si retours communautaires montrent un besoin.

Rationale : effort marginal faible (wrapping de tools déjà existants), bénéfice UX réel pour Claude Desktop (mécanisme natif "joindre une entité"), périmètre tenable.

### D6.2 — Liste des resources V1
🟢 (PO valide la liste, raffinable J1)

| URI | Contenu | Tool source |
|---|---|---|
| `jeedom://install/overview` | Snapshot général install | `get_install_overview` |
| `jeedom://install/health` | État de santé synthétique (daemons, dépendances, messages) | `get_health_summary` |
| `jeedom://scenario/{id}` | Description complète d'un scénario (résolu `#[O][E][C]#`, structure UI-like) | `describe_scenario` + `get_scenario_log` |
| `jeedom://equipment/{id}` | Détail complet d'un équipement (commandes, état, configuration sanitisée) | `get_equipment` |
| `jeedom://logs/today` | Agrégat des logs core + scénarios des dernières 24h | `tail_log` filtré |

### D6.3 — Énumération vs templates
🟡 + 🔵 (détail plafond)

**Approche hybride** : `resources/list` retourne (a) les 2 resources globales overview/health, (b) les N scénarios + équipements les plus récemment actifs (énumération plafonnée), (c) les resources templates (`jeedom://scenario/{id}`, `jeedom://equipment/{id}`) pour les autres.

**Délégué Claude Code J1 (🔵)** : plafond exact (typique : 50 entités énumérées par catégorie). Critères : Claude Desktop reste réactif, lisibilité de la liste, mesure empirique sur la box du PO.

### D6.4 — Pas de duplication tool / resource sur le contrat
🟡 Une resource **ne réinvente pas un schéma** : elle réutilise le schéma de retour du tool homonyme. Maintenance unique. Stabilité semver alignée sur D5.5.

### D6.5 — Pas de prompts V1
🟡 (rappel D1.1) Pas de slash commands V1, candidat roadmap V1.x si retours montrent un besoin de cadrage onboarding.

---

## 7. Relation aux scripts Python existants

### D7.1 — Stratégie de migration
🟡 **Réutilisation par modules de logique** (Option D, intermédiaire entre "porter en PHP" et "réécrire from scratch") :

- **Logique métier reprise** (escape SQL réservés, parsing, graphe d'usage, scenario walker, resolveur `#[O][E][C]#`, blacklist API) — adaptée aux schémas de retour des tools MCP (D5.3) et conventions Python du daemon (typing, async si transport stream, gestion erreurs MCP)
- **Couches d'accès remplacées** (SSH→driver Python local, fichier SSH→fichier local, HTTP distant→HTTP localhost)
- **Setup côté client jeté** (`setup.py`, `_common/credentials.py`, `_common/ssh.py`) — remplacé par config UI Jeedom + hooks plugin

**Mapping** :

| Script jeedom-audit | Module Holmes MCP | Statut |
|---|---|---|
| `db_query.py` | `_core/db.py` (driver Python) | Logique escape conservée, couche d'accès remplacée |
| `logs_query.py` | `_core/logs.py` (lecture fichier) | Validation/résolution conservées, couche SSH remplacée |
| `api_call.py` | `_core/api.py` (HTTP localhost) | Quasi intact, blacklist renforcée selon D4bis.5 |
| `usage_graph.py` | `_domain/usage_graph.py` | Logique conservée, db.py au lieu de ssh.py |
| `scenario_tree_walker.py` | `_domain/scenario_walker.py` | Idem |
| `resolve_cmd_refs.py` | `_domain/cmd_refs.py` | Idem |
| `setup.py` | jeté | Remplacé par hooks plugin + config UI Jeedom |
| `_common/sensitive_fields.py` | `_domain/sanitize.py` | Logique étendue (D16) |

### D7.2 — Organisation interne du daemon Python
🟡 (principe) + 🔵 (détails de découpage)

Structure stratifiée :
- `tools/` — un module par tool MCP D5.3 (25 modules)
- `resources/` — un module par resource MCP D6.2 (5 modules)
- `_core/` — couche d'accès (auth, db, api, logs)
- `_domain/` — logique métier dérivée jeedom-audit (usage_graph, scenario_walker, cmd_refs, sanitize)
- `jeedom/` — package Jeedom natif du template officiel (jeedom_socket, jeedom_com, jeedom_utils)

Détails de nommage et de découpage interne délégués à Claude Code (J0/J1, auto-validation D13.3).

### D7.3 — Pas de copie textuelle "from scratch"
🟡 Le code n'est pas copié-collé tel quel : Claude Code adapte chaque module aux schémas de retour des tools (D5.3) et aux conventions Python du daemon. **La logique métier est conservée, la forme est revue.**

### D7.4 — Référence permanente aux scripts d'origine
🟡 Chaque module de `_domain/` ou `_core/` référence le script jeedom-audit dont il dérive **en commentaire d'en-tête** (« dérivé de scripts/db_query.py de jeedom-audit v1.0.x, commit <sha> »).

À terme, après réalisation de D5.8 et bascule de jeedom-audit consommatrice MCP, les scripts skill peuvent être marqués `DEPRECATED — see holmesMcp tools/<x>` dans le repo jeedom-skills.


---

## 8. Périmètre V1 — synthèse et critères de sortie

### D8.1 — Scope V1 figé
🟡 Le scope V1 listé dans les dimensions 1-8 ci-dessus est **figé** (sauf raffinements internes que Claude Code peut faire en J0/J1 selon résultats du POC D2.3 et de la matrice de couverture D5.8, avec validation PO).

**Inclus V1** : plugin Jeedom natif (PHP + daemon Python), Streamable HTTP, auth Bearer par user Jeedom, accès MySQL via user dédié read-only + logs en lecture fichier + API JSON-RPC localhost, 25 tools (lecture + `query_sql` restreint, dont `get_config` dédié) en 6 familles, 5 resources minimales, sanitisation forte, matrice de couverture skill jeedom-audit, doc + identité produit. Cible OS Debian 12 Bookworm x86_64.

### D8.2 — Politique d'ajout en V1 (anti-drift)
🟡 **Aucune feature non tranchée dans cette session ne rentre en V1.** Si pendant l'exécution un nouveau besoin émerge :
- Si non bloquant → V1.x candidate, ADR ouverte
- Si bloquant pour V1 → ADR + validation PO explicite avant ajout

Rationale : la dérive de scope est le risque n°1 d'un projet binôme PO non-dev / Claude Code. Discipline explicite.

### D8.3 — Critères de sortie V1.0.0
🟡 V1.0.0 est sortable quand **tous les critères suivants sont validés** :

1. POC J0 (D2.3) validé sur la box du PO ✅
2. 25 tools de D5.3 implémentés et testés (unit + intégration sur fixtures synthétiques + tests live via SSH) ✅
3. 5 resources de D6.2 implémentées et testées ✅
4. Auth Bearer par user Jeedom fonctionnel sur Claude Desktop **et au moins un autre client MCP** (Cursor ou MCP Inspector) ✅
5. Sanitisation (D16) validée par le PO sur sa propre install (sanity check à l'œil humain — D15.6) ✅
6. Matrice de couverture skill jeedom-audit (D5.8) produite et lue par le PO ✅
7. README + identité produit Holmes MCP rédigée ✅
8. Plugin packagé installable depuis sources (avant soumission market) ✅
9. **Documentation utilisateur officielle complète** publiée sur GitHub Pages, référencée dans `info.json`, lue et validée par le PO avant soumission market (D12.6.bis) ✅

### D8.4 — Phase bêta privée → release publique market
🟡 V1.0.0 sortable ≠ V1.0.0 publique sur le market.

**Phase bêta privée** entre les deux :
- Plugin testé sur la **seule box du PO pendant au moins 2 semaines d'usage réel** par le PO
- Aucun crash daemon pendant cette période
- Aucune fuite de données identifiée par les sanity checks PO
- Au moins **5 sessions Claude Desktop / Cursor réelles** menées par le PO avec usage normal du plugin (pas juste "ça démarre")

Une fois les 3 conditions OK → soumission market **directement en statut "bêta"**, pas en "stable". Conversion bêta → stable après quelques semaines de retours communautaires positifs (à arbitrer en exécution, pas dans ce brief).

Pas de programme bêta privé externe en V1 (pas de beta-testeurs externes recrutés avant release market). Les retours communautaires viendront via la bêta market.

---

## 9. Stack technologique

> **Note** : toutes les décisions stack sont déjà tranchées par les dimensions 2, 4 et 4bis. Cette section consolide pour Claude Code et trance les choix résiduels.

### Stack acquise (rappel)

| Couche | Choix | Décision source |
|---|---|---|
| Plugin Jeedom (enveloppe market) | PHP (langage natif Jeedom) | D2.1, D2.2 |
| Daemon serveur MCP | Python 3.11+ | D2.1 |
| SDK MCP | SDK MCP Python officiel d'Anthropic | D2.1 |
| Transport MCP | Streamable HTTP (spec 2025-03-26+) | D3.1 |
| Driver MySQL | PyMySQL recommandé (à confirmer J0) | D4bis.1 |
| Communication interne PHP↔Python | Mécanismes Jeedom standards (`jeedom_socket`, `jeedom_com`, callback PHP) | doc Jeedom |
| Auth MCP externe | Bearer token, lookup map token→user Jeedom | D4.1, D4.2 |
| Gestion dépendances | `packages.json` (apt + pip3) Jeedom 4.4.9+, venv natif core | D2.4 |
| OS cible V1 | Debian 12 Bookworm x86_64 + Jeedom 4.5+ | D2.4 |
| Version spec MCP | Dernière stable J0 (4 critères) | D1.2 |

### D9.1 — Bibliothèques Python complémentaires
🔵 **Délégué Claude Code J0.**

Au-delà du SDK MCP officiel et du driver MySQL, le daemon aura besoin de bibliothèques pour :
- Requêtes HTTP vers API JSON-RPC Jeedom localhost (`requests` ou `httpx`)
- Parsing SQL pour `query_sql` restreint (`sqlparse` ou parser custom)
- Logging structuré (`structlog` ou `logging` stdlib)
- Tests (`pytest` + `pytest-asyncio` si async)

**Critères pour Claude Code J0** :
1. Privilégier les bibliothèques **standards et matures** (PyPI top 1000, maintenance active)
2. Minimiser le nombre de dépendances tierces (chaque dep = un risque de friction install)
3. Toutes les deps doivent être déclarables proprement dans `packages.json` (section `pip3`)
4. Documenter en ADR le choix final et les versions épinglées

**Reco par défaut** :
- HTTP : `httpx` si daemon async, `requests` sinon
- Parsing SQL : `sqlparse` (éprouvé) — ou parser custom léger si SELECT-only suffit
- Logs : `structlog` recommandé pour D15 si pas de friction install ; sinon `logging` stdlib avec formatter JSON

### D9.2 — Pas de framework web tiers
🟡 Le daemon MCP **ne dépend pas d'un framework web** (pas de Flask, FastAPI, Django, aiohttp...). Le SDK MCP Python officiel embarque déjà son propre serveur HTTP pour Streamable HTTP.

Rationale : ajouter un framework web par-dessus le SDK MCP = duplication, conflits potentiels, surface d'attaque accrue.

### D9.3 — Pas d'ORM
🟡 Le daemon **n'utilise pas d'ORM** (pas de SQLAlchemy ni équivalent). Accès MySQL via driver bas niveau + requêtes SQL paramétrées (réutilisation logique `db_query.py` jeedom-audit).

Rationale : ORM = courbe d'apprentissage, schéma à modéliser, abstraction qui complique le diagnostic. La logique de jeedom-audit est SQL direct, on garde la même approche pour cohérence et lisibilité.

### D9.4 — Pas de base de données interne au plugin
🟡 Le plugin **ne crée aucune table propre** dans MySQL Jeedom (en V1). Toute donnée plugin (config, token utilisateur, etc.) est stockée via les mécanismes Jeedom standards :
- `config::save()` / `config::byKey()` pour la config plugin
- `User->setOption()` / `User->getOption()` pour les tokens par utilisateur (pattern `specialAttributes.user`)

Rationale : pas de schéma DB propre = pas de migration à gérer entre versions = simplicité de maintenance.

---

## 10. Structure du repo

### D10.1 — Structure des fichiers
🟡 Structure conforme au plugin template Jeedom officiel + organisation interne D7.2 :

```
holmesMcp/                              ← repo GitHub public, racine = plugin Jeedom
│
├── plugin_info/
│   ├── info.json                       ← manifeste (cf. doc info.json)
│   ├── packages.json                   ← deps apt + pip3 (méthode moderne)
│   ├── install.php                     ← hooks holmesMcp_install/update/remove
│   ├── changelog.md                    ← changelog versionné
│   └── holmesMcp_icon.png              ← icône market (Holmes-themed)
│
├── core/
│   ├── class/
│   │   └── holmesMcp.class.php         ← classe eqLogic + méthodes deamon_*
│   ├── ajax/
│   │   └── holmesMcp.ajax.php          ← endpoints AJAX UI
│   └── php/
│       ├── holmesMcp.inc.php           ← helpers internes PHP
│       └── jeeholmesMcp.php            ← callback daemon→PHP (cf. doc daemon)
│
├── desktop/
│   ├── php/
│   │   └── holmesMcp.php               ← vue config plugin (token par user, port, état)
│   ├── js/
│   │   └── holmesMcp.js                ← JS de la vue config
│   └── modal/
│       └── modal.holmesMcp.php         ← modaux éventuels
│
├── resources/
│   ├── holmesMcpd/                     ← convention Jeedom : <pluginID>d/
│   │   ├── holmesMcpd.py               ← entrypoint daemon (template adapté)
│   │   ├── mcp_server.py               ← bootstrap MCP, registration tools/resources
│   │   ├── tools/                      ← 25 modules (un par tool D5.3)
│   │   ├── resources/                  ← 5 modules (un par resource D6.2)
│   │   ├── _core/                      ← auth.py, db.py, api.py, logs.py
│   │   ├── _domain/                    ← usage_graph, scenario_walker, cmd_refs, sanitize
│   │   └── jeedom/                     ← package Jeedom natif (du template)
│   │       └── jeedom.py
│   └── requirements.txt                ← référence — vraie source = packages.json
│
├── docs/                               ← doc projet (pour Claude Code, pas market)
│   ├── README.md                       ← index navigation
│   ├── PLANNING.md                     ← ce brief une fois ingéré
│   ├── decisions/                      ← ADRs
│   ├── state/
│   │   ├── PROJECT_STATE.md            ← état projet (continuité sessions)
│   │   └── CONTRIBUTING-CLAUDE-CODE.md ← contrat opérationnel binôme PO/CC
│   ├── sessions/                       ← journal sessions Claude Code
│   ├── skill-coverage-matrix.md        ← D5.8 : mapping WF skill ↔ tools MCP
│   ├── ROADMAP.md                      ← roadmap V1.x / V2+
│   └── user/                           ← source MkDocs pour doc utilisateur publique
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── live/                           ← checklists pour validation live (one-liner SSH)
│   ├── fixtures/
│   │   └── synthetic/                  ← fixtures synthétiques publiques
│   └── conftest.py
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      ← lint + tests unit + intégration synthétique
│       └── docs.yml                    ← build & deploy doc MkDocs sur gh-pages
│
├── README.md                           ← README market-friendly + identité Holmes
├── LICENSE                             ← AGPL-3.0
├── .gitignore                          ← strict (cf. D11.8)
├── .gitattributes                      ← cf. doc Jeedom : import market
└── pyproject.toml                      ← config Python (linter, tests)
```

### D10.2 — Racine du repo = racine du plugin
🟡 Le repo GitHub a directement le contenu du plugin à la racine (pas de sous-dossier intermédiaire). Convention market Jeedom.

### D10.3 — Doc projet (`docs/`) embarquée vs séparée
🔵 **Délégué Claude Code J0.**

**Critères pour Claude Code** :
1. Si `docs/` embarqué dans l'install pose un problème de poids ou de propreté market → branche `develop` pour la doc, `main` propre
2. Sinon (cas par défaut) → tout dans `main`, plus simple à maintenir
3. À arbitrer après vérification du processus de packaging market réel
4. Documenter en ADR

### D10.4 — Licence
🟢 **AGPL-3.0** pour Holmes MCP.

**Bascule conjointe `jeedom-skills` MIT → AGPL-3.0** acté en parallèle de la sortie V1 Holmes MCP, pour cohérence sphère.

**Conditions opérationnelles** :
- Bascule conditionnée à confirmation **PO seul copyright holder** sur le repo `jeedom-skills` (vérification J0 par Claude Code via `git log`)
- Si contribution externe identifiée → soit consentement obtenu, soit code concerné réécrit/retiré, soit fallback discuté avec PO (option : tout MIT)
- ADR de relicence dans `jeedom-skills` + entrée `CHANGELOG.md` + commit dédié
- Communication forum Jeedom au moment de la sortie V1 Holmes MCP (annonce conjointe alignement licence)

Rationale : alignement écosystème Jeedom officiel (core AGPL), cohérence sphère jeedom-audit + Holmes MCP, garantie que toute évolution dérivée du code reste accessible à la communauté. Le coût d'adoption tierce est négligeable dans ce contexte (outil de niche pour la communauté Jeedom francophone).

### D10.5 — Stratégie de branches Git
🟡
- **`main`** → branche stable, pointée par les releases tag (convention GitHub par défaut depuis 2020, alignement avec le repo officiel `jeedom/core` qui utilise également `main`)
- **`develop`** → branche d'intégration courante (où Claude Code travaille)
- Branches features ad hoc fusionnées dans `develop`

### D10.6 — Politique de tag et releases
🟡
- **Tags semver** alignés sur D5.5 : `v1.0.0`, `v1.0.1`, `v1.1.0`, `v2.0.0`
- **Releases GitHub** créées à chaque tag stable, avec notes générées depuis `changelog.md`
- **Pre-releases** (`v0.1.0`, `v0.2.0`, ...) pour les jalons J0-Jn internes

### D10.7 — Pas de submodule vers jeedom-audit
🟡 La matrice de couverture (D5.8) référence les workflows et scripts de jeedom-audit. **Pas de submodule git** (couplage trop fort), mais lien explicite dans `docs/skill-coverage-matrix.md` vers les **commits/tags précis** de jeedom-audit auxquels la matrice fait référence.

Rationale : si jeedom-audit évolue, on sait à quel snapshot la matrice se rapporte sans couplage technique.

### D10.8 — Nom et identité du plugin
🟢 + 🔵 (vérification disponibilité ID en J0)

**ID Jeedom** : `holmesMcp` (camelCase).
**Nom human-readable** : "Holmes MCP".

**Identité produit (encadré pour la doc et le README)** :
> Holmes MCP : Holmes observe, déduit, raconte. Il ne touche jamais à la scène, sans jamais exposer les secrets de votre maison. Plugin Jeedom natif open source qui expose la box Jeedom comme serveur MCP en lecture seule, orienté audit, diagnostic et assistance à la conception. Pour Claude Desktop, Cursor et tout client MCP compatible.

**Délégué Claude Code J0 (🔵)** :
1. Vérifier que `holmesMcp` est libre comme ID Jeedom market
2. Vérifier qu'il n'y a pas de collision marque évidente sur l'écosystème domotique francophone (recherche rapide "Holmes" + domotique/Jeedom)
3. Si conflit identifié → escalade au PO avec alternatives (`jeedoscope`, `vigieMcp`, `holmesMcpAudit`, autre)

Rationale : l'identité narrative "Holmes" — observateur méthodique, déductif, discret — colle parfaitement au positionnement produit (audit, lecture seule, sanitisation forte). Le suffixe `Mcp` clarifie la fonction sans alourdir le nom. La séparation entre ID technique camelCase et nom human-readable suit la convention market Jeedom.

---

## 11. Tests

### D11.1 — Pyramide de tests
🟡
- **Tests unitaires** (`tests/unit/`) : >80 % couverture sur `_core/` et `_domain/`, écrits et exécutés par Claude Code en CI, **pas de dépendance PO**
- **Tests d'intégration** (`tests/integration/`) : DB MySQL Docker + fixtures synthétiques publiques (`tests/fixtures/synthetic/`), exécutés par Claude Code en CI ; pas d'API JSON-RPC ni client MCP réels en CI
- **Tests live** (`tests/live/`) : Claude Code via SSH (alias `Jeedom` opérationnel sur sa machine de dev — D11.7) sur la box du PO, fixtures réelles privées (hors repo), aucune action opérationnelle PO

### D11.2 — Fixtures de test
🟡 **Deux jeux** :

- **Fixtures synthétiques** : générées par Claude Code, versionnées dans le repo (`tests/fixtures/synthetic/`), utilisées en CI publique. Le schéma DB Jeedom est public, les conventions sont publiques, les fixtures sont entièrement constructibles sans dump réel.

- **Fixtures depuis box réelle** : récupérées par Claude Code via SSH, sanitisation automatique par script Claude Code, stockées **hors-repo** (workspace local Claude Code uniquement). Utilisées pour tests d'intégration spécifiques nécessitant des données réelles que Claude Code ne peut pas inférer du schéma seul.

### D11.3 — Outils de test
🟡 **MCP Inspector** + un client MCP de test (Claude Desktop ou Cursor configurés sur la machine Claude Code) pointant le daemon de la box via réseau LAN ou SSH tunnel. **Le PO ne configure rien.**

Validation Claude Desktop sur la machine PO : uniquement avant V1.0.0 (critère D8.3 #4 — un test ponctuel par release).

### D11.4 — Tests live exécutés par Claude Code via SSH
🟡 À chaque jalon nécessitant validation live, Claude Code automatise :
1. Build du plugin (zip)
2. Upload sur la box via SCP/SSH
3. Installation côté Jeedom
4. Démarrage du daemon
5. Exécution des smoke tests
6. Restitution dans la session : ✅ tout vert ou ❌ avec stack trace

**Aucune action opérationnelle PO**. Le PO valide en relisant le résumé de session.

### D11.5 — Pas d'évals automatisées de qualité LLM en V1
🟡 On ne mesure pas en CI la qualité de réponse du LLM consommant le MCP (≠ jeedom-skills qui a un harness d'évals). C'est un sujet roadmap V1.x.

Rationale : la qualité de réponse du LLM dépend du LLM côté client, pas du serveur MCP. Les tests fonctionnels du serveur (entrée → sortie déterministe) suffisent pour qualifier le serveur lui-même.

### D11.6 — CI GitHub Actions minimale
🟡 + 🔵 (détails outils lint/format)

- Lint Python (`ruff` recommandé — délégué J0)
- Tests unitaires + intégration via Docker (avec MySQL container) sur fixtures synthétiques uniquement
- **Pas d'accès SSH en CI publique** (impossible : pas de box Jeedom dans CI)
- Workflow déclenché sur push `develop` et PR vers `main`

**Délégué Claude Code J0 (🔵)** : choix exact lint/format (`ruff`, `flake8`, `black` ou autre), version Python testée en CI (3.11+).

### D11.7 — Cadre d'usage de l'accès SSH PO par Claude Code
🟡 Cf. section 0.4 de ce brief (modèle opérationnel). Conditions d'usage :
- Actions limitées au plugin Holmes MCP
- Aucune commande destructive sans validation PO explicite
- Aucune modification non autorisée hors plugin
- Logs des actions SSH dans `docs/sessions/` pour traçabilité PO
- En cas de doute, demande PO avant action

### D11.8 — Isolation totale des credentials et de la configuration d'accès
🟡 Cf. section 0.5 de ce brief. **Non négociable.**

- `.gitignore` strict (couvre `~/.ssh/*`, `*.creds`, `*credentials*.json`, `.env`, `.env.local`, dump SQL bruts, fixtures réelles non sanitisées)
- **Pre-commit hook** : scan automatique du commit pour patterns sensibles (regex IP, regex token format, hostnames courants, etc.) — refus du commit si détection
- **Pre-push hook** : second scan avant push GitHub
- **Review systématique de chaque PR** vers `main` avec checklist credentials avant merge
- Procédure de réponse rapide en cas de leak : rewrite git history, force push, rotation immédiate du credential, ADR d'incident

Pas de credential, IP, hostname, alias SSH, user MySQL, port, mot de passe, token, apikey, chemin absolu PO-spécifique, ou identifiant lié à l'environnement PO dans le repo, jamais.

---

## 12. Distribution et maintenance

### D12.1 — Plateforme de distribution
🟡 **Market Jeedom** (officiel) en voie nominale. Pas de distribution alternative en V1 (pas de NextDom Alternative Market activement, pas de release GitHub indépendante recommandée à l'utilisateur lambda).

Releases GitHub maintenues comme source canonique pour les power users qui veulent suivre le code, mais voie d'install nominale = market.

### D12.2 — Statut de release
🟡 **V1.0.0 publié en statut "bêta"** sur le market (cf. D8.4). Conversion en "stable" après période d'observation des retours communautaires (à arbitrer en exécution).

### D12.3 — Version Jeedom minimale supportée
🟡
- `info.json` `"require": "4.5"` (matrice D2.4)
- Politique de support : **Jeedom N et N-1** (alignement jeedom-skills). Quand Jeedom 4.6 sortira, support 4.5 + 4.6, 4.4 déprécié
- Mention claire dans le README de la matrice de compatibilité

### D12.4 — Versionnement
🟡 Semver strict (rappel D5.5) : `1.0.0` / `1.0.x` / `1.x.0` / `2.0.0`. Tags GitHub à chaque release. Pre-releases (`v0.x.0`) pour jalons J0-Jn internes.

### D12.5 — Stratégie d'évolution MCP
🟡
- V1 cible une version précise de la spec MCP (D1.2)
- Support N et N-1 (versions de la spec MCP)
- Breaking changes côté spec MCP → version majeure Holmes MCP avec migration guide
- ADR à chaque adoption d'une nouvelle révision spec

### D12.6 — Documentation utilisateur officielle
🟡 + 🔵 (détails MkDocs)

**Documentation officielle obligatoire** référencée dans `info.json` (champs `documentation` + `documentation_beta`). Sans elle, pas de validation market Jeedom.

**Hébergement** : **GitHub Pages avec MkDocs Material**, source dans `docs/user/` du repo. Build automatisé via GitHub Actions (`.github/workflows/docs.yml`).

URL : `https://<user>.github.io/holmesMcp/`.

**Plan obligatoire (12 sections)** :
1. Présentation et identité produit
2. Prérequis OS et Jeedom
3. Installation via market
4. Configuration du plugin (tokens par user, port)
5. Configuration des clients MCP (Claude Desktop, Cursor, MCP Inspector)
6. Sécurité (HTTPS hors LAN, rotation tokens, mécanismes de sanitisation)
7. Liste des 25 tools avec exemples d'usage en langage naturel
8. Liste des 5 resources avec usage
9. Diagnostic et logs (lien vers D15)
10. FAQ / Troubleshooting
11. Lien vers la sphère jeedom-audit
12. Contribuer / signaler un bug

**Versioning** : doc taguée `vX.Y.Z` alignée sur le plugin, sélecteur de version dans la navigation, changelog dédié.

**Captures d'écran** : matière fournie par le PO sur demande explicite et timée de Claude Code (cf. section 0.2.e). Demandes groupées par jalon.

**Délégué Claude Code J0 (🔵)** :
1. Setup MkDocs Material avec navigation, sélecteur de version, recherche, dark mode
2. CI GitHub Actions qui rebuild la doc à chaque push sur `main` et publie sur `gh-pages`
3. Validation que l'URL `gh-pages` est accessible avant le premier renseignement de `info.json`
4. ADR du choix de stack doc

### D12.6.bis — Documentation comme livrable critique V1.0.0
🟡 **Critère #9 de sortie V1.0.0** (D8.3) : doc complète publiée sur GitHub Pages, référencée dans `info.json`, lue et validée par le PO avant soumission market.

Rationale : élever la doc au rang de critère de sortie pour qu'elle ne soit pas l'item bâclé en fin de release sous pression de sortie.

### D12.7 — Procédure de release
🟡 + 🔵 (détails soumission market)

Claude Code automatise :
1. Tests unit + intégration verts en CI
2. Tests live exécutés via SSH par Claude Code, validés
3. Mise à jour `changelog.md` + `info.json` (version)
4. Commit + tag semver + push
5. Build du zip plugin
6. Soumission market (action PO si étape manuelle, sinon Claude Code via API si disponible)
7. Annonce forum Jeedom (rédigée par Claude Code, validée par PO)

Le PO valide chaque étape via les résumés de session, n'exécute aucune commande hors soumission market et publication forum.

**Délégué Claude Code J0 (🔵)** : confirmation des étapes manuelles vs automatisables selon ce que permet l'API/UI développeur Jeedom à ce moment.

### D12.8 — Maintenance corrective
🟡
- Bugs critiques (fuite données, crash daemon, faille de sécurité) : patch dans les **48h** (V1.0.x), annonce forum
- Bugs majeurs (tool retournant mauvaise donnée, install échouant sur certains setups) : patch dans la **semaine**
- Bugs mineurs : patch lors de la prochaine release minor planifiée

Sources de remontée : issues GitHub + thread forum dédié + retours via le projet Claude.

### D12.9 — Maintenance évolutive et roadmap
🟡 Pas de cadence fixe. Évolutions rythmées par :
- Retours communauté (priorisation par PO)
- Évolutions de la spec MCP
- Nécessités de la sphère jeedom-audit (D5.8 et bascule future)

Roadmap maintenue dans `docs/ROADMAP.md` par Claude Code à partir des décisions PO. Mise à jour à chaque session significative.

---

## 13. Modèle opérationnel PO / Claude Code

> **Note** : la section 0 de ce brief pose le modèle opérationnel complet. Cette section consolide les décisions formelles.

### D13.1 — Adoption du contrat opérationnel jeedom-skills section 0
🟡 Le contrat PO/Claude Code de jeedom-skills (section 0 de l'idéation output) est adopté par défaut pour Holmes MCP, avec les ajustements suivants :
- Claude Code dispose d'un accès SSH à la box (D11.7, D11.8, section 0.4)
- Plus de tâches techniques sont automatisées par Claude Code (cf. tableau ci-dessous)
- Les goulets d'étranglement physiques sont explicitement listés (section 0.2.e)

Le contrat est rédigé par Claude Code en `docs/state/CONTRIBUTING-CLAUDE-CODE.md` au J0 et soumis au PO pour validation.

### Tâches automatisées par Claude Code (différence vs jeedom-skills)

| Tâche | Jeedom-skills | Holmes MCP |
|---|---|---|
| Setup initial du plugin sur la box | n/a | Claude Code via SSH |
| Tests live exécution | PO | Claude Code via SSH |
| Récupération de fixtures réelles | PO | Claude Code via SSH |
| Lecture des logs daemon en debug | PO | Claude Code via SSH |
| Vérification d'état post-déploiement | PO | Claude Code via SSH |
| Captures d'écran UI Jeedom | PO | PO (Claude Code n'a pas X11 fiable) |
| Validation finale Claude Desktop | n/a | PO (UI sur sa machine perso) |
| Sanity check sanitisation | PO | PO (œil humain qui connaît son install) |
| Soumission market | n/a | PO (compte développeur PO) |
| Réponses sur le forum communautaire | PO | PO (identité PO) |
| Validation des décisions / orientation | PO | PO |

### D13.2 — Demandes structurées avec options
🟡 Quand un arbitrage est nécessaire, Claude Code présente 2 à 4 options claires avec leurs trade-offs et une recommandation par défaut. Le PO accepte, choisit autre, ou demande à débattre. Pas de questions ouvertes "comment veux-tu faire X ?".

### D13.3 — Auto-validation des choix triviaux
🟡 Conventions de nommage internes, organisation de fichiers internes, choix de variables, formulations mineures dans les drafts → Claude Code décide seul. Pas de gaspillage de cycles de validation sur des détails.

### D13.4 — Demandes de matières physiques explicites et timées
🟡 Pour les goulets d'étranglement physiques, Claude Code formule des demandes :
- **Explicites** : "À l'étape J7.4, j'ai besoin de…"
- **Timées** : "…d'ici la fin de cette session" ou "avant J7"
- **Groupées** : plutôt que fractionner ("captures de J7 + validation Claude Desktop + cross-check sanitisation des nouvelles fixtures") → 1 sollicitation PO unique pour N matières
- **Avec spec précise** : format, résolution, contenu attendu

### D13.5 — Sessions courtes orientées avancement
🟡 Préférence pour plusieurs sessions ciblées avec validation PO entre les deux, à une session marathon qui produit beaucoup sans validation intermédiaire.

Critère : à la fin de chaque session, le PO doit pouvoir comprendre ce qui a été produit en lisant le résumé de session, pas en relisant tout le code.

### D13.6 — Continuité entre sessions (routine début)
🟡 Cf. section 0.3 de ce brief. À chaque début de session, Claude Code lit dans l'ordre :
1. `docs/README.md`
2. `docs/state/PROJECT_STATE.md`
3. ADRs récentes
4. Dernière entrée `docs/sessions/`
5. Annonce au PO de l'état + objectifs de la session

### D13.7 — Routine de fin de session
🟡 À chaque fin de session significative :
1. Mise à jour `docs/state/PROJECT_STATE.md`
2. Nouvelle entrée `docs/sessions/`
3. ADR(s) si décisions non triviales prises
4. Commit + tag pre-release si jalon

### D13.8 — Fréquence des sessions
🟡 Pas de cadence imposée. Le PO déclenche les sessions selon sa disponibilité. Claude Code n'attend rien hors session, ne suit pas de calendrier.

Si une session est très espacée de la précédente (> 2 semaines), Claude Code applique D13.6 (relecture complète de l'état) au démarrage et le mentionne explicitement au PO.

### D13.9 — Communication entre sessions
🟡 Pas de canal asynchrone entre sessions Claude Code. Toute communication PO→Claude Code passe par les sessions. Le PO note ses idées/feedback dans un fichier scratch local ou directement à l'ouverture de la session suivante.

### D13.10 — Si un goulet d'étranglement bloque
🟡 Si une session se termine en attendant matière du PO (capture, validation), Claude Code :
1. Met à jour `PROJECT_STATE.md` avec un statut clair "EN ATTENTE de [matière X]"
2. Liste les tâches qui peuvent avancer en parallèle (autres jalons indépendants)
3. Le PO peut soit fournir la matière, soit demander à avancer sur les autres tâches


---

## 14. Observabilité

> **Concept (encadré factuel)** — Trois canaux de logs distincts dans le système : (1) **logs daemon Holmes MCP** (sujet de cette dimension), (2) **logs Jeedom natifs** (lus *par* Holmes MCP via tool `tail_log`, pas le sujet ici), (3) **logs côté client MCP** (Claude Desktop, Cursor — hors scope plugin). Cette dimension traite uniquement le canal 1.

### D14.1 — Format des logs daemon
🟡 **JSON Lines** (un objet JSON par ligne). Schéma de log standardisé :

```json
{
  "ts": "2026-05-02T14:32:01.123Z",
  "level": "info",
  "request_id": "uuid-...",
  "user": "guillaume",
  "client": "claude-desktop/1.5",
  "tool": "list_scenarios",
  "params": { "active": true },
  "duration_ms": 45,
  "result": "ok",
  "rows_returned": 12,
  "filtered_fields": []
}
```

Niveaux : `debug`, `info`, `warning`, `error`, `critical`.

### D14.2 — Emplacement des logs daemon
🟡 Fichier de log Jeedom standard, accessible via `log::getPathToLog('holmesMcp_daemon')` côté PHP, écrit en JSON Lines par le daemon Python. Affiché dans le cadre "Logs" natif de la page config plugin.

Rotation logarithmique standard Jeedom (gérée par le core, pas par Holmes MCP).

### D14.3 — Niveau de log par défaut
🟡 **`info` en V1**, configurable dans la page de config plugin (dropdown : `debug` / `info` / `warning` / `error`).

- `info` = chaque requête MCP loggée avec son outcome, pas les détails internes
- `debug` = traces SQL, traces HTTP API JSON-RPC, traces internes daemon. Réservé au debug, peut être verbose.

### D14.4 — Vue dédiée logs Holmes MCP dans la page de config plugin
🟡 + 🔵 (détails UI)

Vue dédiée dans la page de config Holmes MCP (onglet "Activité" ou "Logs Holmes") qui parse le JSON Lines et l'affiche en tableau lisible :

| Date/heure | Utilisateur | Tool appelé | Paramètres résumés | Durée | Résultat |
|---|---|---|---|---|---|
| 14:32:01 | guillaume | list_scenarios | active=true | 45ms | ✅ 12 résultats |
| 14:32:15 | guillaume | get_scenario | id=12 | 32ms | ✅ |
| 14:32:23 | guillaume | query_sql | rejected | — | ❌ DELETE non autorisé |

Filtres : par utilisateur, par tool, par niveau, par fenêtre temporelle (dernière heure / jour / 7 jours).

**Délégué Claude Code J1 (🔵)** : framework JS, refresh auto, filtres précis. Critère : la vue doit fonctionner dans l'UI Jeedom standard sans dépendance JS exotique.

### D14.5 — Règles de log
🟡 **Chaque requête MCP entrante** logue :
- Identité de l'utilisateur (résolu depuis le token Bearer, D4.7)
- Nom du tool ou resource appelé(e)
- Paramètres **sanitisés** (cf. D16 — pas de credentials qui passeraient en paramètres)
- Durée d'exécution
- Outcome (ok / erreur, avec type d'erreur)
- Volumes (nombre de résultats, nombre de champs filtrés par sanitisation)

**Ce qui n'est pas loggué** :
- Le contenu des résultats (peut être volumineux et sensible)
- Le contenu intégral des paramètres SQL d'un `query_sql` au-delà d'un résumé (~100 premiers caractères + flag SELECT-only validé)
- Les credentials sous quelque forme
- Les contenus de `configuration` JSON eqLogic même filtrés

### D14.6 — Logs d'erreur enrichis
🟡 Quand une erreur survient, le log inclut :
- `error_type` (ex. `tool_not_found`, `sql_rejected`, `db_connection_lost`, `auth_failed`)
- `error_message` (court, lisible)
- `traceback` (uniquement si niveau `debug`, jamais en `info`)
- `request_id` (pour corréler avec la requête entrante)

Pour le PO, la vue UI affiche `error_type` + `error_message`. Bouton "voir détails techniques" qui révèle traceback si log au niveau `debug`.

### D14.7 — Pas de télémétrie externe
🟡 **Aucun log ne quitte la box.** Pas de Sentry, Datadog, télémétrie Anthropic, ou autre. Tout reste local.

Rationale : conformité au principe de privacy de la sphère jeedom-audit/Holmes MCP.

### D14.8 — Diagnostic guidé pour le PO non-dev
🟡 Section "Diagnostic" dans la doc utilisateur (D12.6 plan #9) qui guide le PO non-dev avec un arbre de décision :

> **Mon Claude Desktop me donne une réponse étrange. Que faire ?**
>
> 1. Ouvrir la page Holmes MCP dans Jeedom → onglet Activité
> 2. Filtrer sur la dernière minute
> 3. **Si la requête est loggée avec Résultat ✅** → le plugin a fait son travail. Le LLM a mal interprété, soit la requête, soit la réponse. Reformulez.
> 4. **Si Résultat ❌** → notez le `Type d'erreur` et le `Message`. FAQ ou issue avec ces infos.
> 5. **Si rien dans le log** → le client MCP n'a pas pu joindre le plugin. Vérifiez : token correct, port accessible, daemon démarré.

### D14.9 — Logs daemon distincts des logs plugin PHP
🟡 Le plugin PHP Jeedom écrit ses logs (install, démarrage daemon, erreurs PHP) dans `holmesMcp` (sans suffixe). Le daemon Python écrit dans `holmesMcp_daemon`. **Deux fichiers distincts**.

Cohérent avec le pattern Jeedom standard. La vue UI peut afficher les deux séparément (onglets "Plugin" et "Daemon").

---

## 15. Sanitisation et guardrails

> **Concept (encadré factuel)** — La base Jeedom contient des données sensibles : tokens API plugins (Aqara, Tuya, Hue…), creds MQTT/broker, apikeys, mots de passe utilisateurs, configurations JSON imprévisibles. Sans filtrage, ces données partent vers les LLMs externes lors d'une requête innocente. Risques : stockage par le LLM dans ses logs, partage public d'une conversation, prompt injection ciblée. La sanitisation est un **trait identitaire** de Holmes MCP, au même titre que la lecture seule V1.

### D15.1 — Stratégie de sanitisation à 3 mécanismes
🟡 **Trois mécanismes cumulés** (défense en profondeur) :

1. **Whitelist de champs exposables** sur tables connues (`eqLogic`, `cmd`, `scenario`, etc.). Tout champ hors whitelist est masqué par défaut.
2. **Regex sur clés JSON** des blobs `configuration`/`options`/`value` : `(?i)(password|pwd|token|apikey|api_key|secret|hash|credentials|auth|cert|private_key|access_key|client_secret|bearer)`
3. **Liste hard-codée par plugin connu** : couvre les nommages exotiques connus (clés `configuration` plugin-spécifiques)

**Comportement** : **Mask + count** — champs remplacés par `***FILTERED***` dans la sortie + tableau `_filtered_fields` joint à chaque réponse pour transparence LLM-side.

Rationale : drop silencieux risque hallucination LLM ; mask + count permet au LLM d'expliquer à l'utilisateur "ce champ est masqué pour votre sécurité".

### D15.2 — Liste de regex et hard-codes de référence
🟡 + 🔵 (enrichissement liste hard-codée J1)

Module `_domain/sanitize.py` dérivé de `_common/sensitive_fields.py` jeedom-audit, enrichi.

**Liste regex initiale** : `password|pwd|token|apikey|api_key|secret|hash|credentials|auth|cert|private_key|access_key|client_secret|bearer` (case-insensitive).

**Liste de plugins hard-codés au minimum V1** : jMQTT (broker creds), Aqara, Tuya, Hue, Telegram, OpenWeatherMap, MQTT Manager, Mobile.

**Délégué Claude Code J1 (🔵) : enrichissement de la liste hard-codée** par revue rapide des 10 plugins Jeedom les plus installés.

**Critères pour Claude Code J1** :
1. Lecture des README/sources des 10 plugins Jeedom les plus installés (statistique market)
2. Identification des clés `configuration` qui contiennent des credentials
3. Ajout à la liste hard-codée
4. ADR de la liste V1.0.0 + procédure de mise à jour communautaire (issues GitHub)

### D15.3 — Refus de `query_sql` qui cible des champs sensibles
🟡 Le tool `query_sql` (D5.6) parse la requête SQL avant exécution. Si la requête fait référence à :
- Table `config`
- Colonnes nommées `password`, `token`, `apikey`, `secret`, `hash`, `credentials`...
- Patterns `WHERE x LIKE '%token%'` ciblant les noms

→ **Refus 400** avec message explicite, log de la tentative en niveau `warning` (pas `error`, c'est un refus défensif).

### D15.4 — Sanitisation des logs
🟡 (rappel D14.5) Chaque entrée de log applique le même sanitiseur que les réponses MCP. **Pas de credential dans les logs même partiellement** — masquage complet `***FILTERED***`.

### D15.5 — Tests exhaustifs de la sanitisation
🟡 **Tests unitaires obligatoires** (`tests/unit/sanitize/`) :
- Liste de fixtures avec credentials connus dans tous les emplacements (eqLogic.configuration, cmd.configuration, config table, dataStore, etc.)
- Pour chaque fixture, vérifier que la sortie sanitisée ne contient **aucune occurrence** des credentials originaux
- **Couverture cible : 100 % du module `sanitize.py`**

**Tests d'intégration** : appel des tools sur fixtures réelles privées (récupérées via SSH par Claude Code, hors-repo), inspection automatique de la sortie pour vérifier absence de tout pattern sensible.

### D15.6 — Sanity check PO sur installation réelle
🟡 **Avant V1.0.0** : Claude Code exécute Holmes MCP sur la box réelle du PO via SSH, lance les tools les plus exposants (`get_equipment` sur tous les eqLogics, `query_sql SELECT * FROM eqLogic LIMIT 10`, `tail_log core`...), et fournit au PO un **rapport de sortie sanitisée** que le PO **lit et valide à l'œil humain**.

Le PO connaît son install, repère ce qui ne devrait pas y être. Ce sanity check humain est **non négociable** (la regex et les whitelists peuvent rater quelque chose de spécifique à son install).

Aligné avec section 0.2.e : sanity check sanitisation = goulet d'étranglement physique.

### D15.7 — Procédure de réponse rapide en cas de fuite
🟡 Issues GitHub avec template "Champ sensible non filtré" → patch rapide en V1.0.x (D12.8 critique 48h).

Si une fuite est rapportée publiquement, **procédure de réponse rapide** :
- Patch sous 24h
- Issue GitHub publique avec rationale
- Annonce forum Jeedom
- Communication communautaire transparente
- ADR d'incident

### D15.8 — Pas de tool exposant explicitement des credentials
🟡 **Aucun tool de la liste D5.3 ne demande, ne retourne, ne manipule des credentials.** Pas de `get_plugin_credentials`, `get_user_password`, etc.

Si un utilisateur a besoin de récupérer un credential, il passe par l'UI Jeedom, pas par MCP. La sanitisation est un **filet de sécurité**, pas une fonctionnalité métier.

### D15.9 — Documentation sécurité dans la doc utilisateur
🟡 Dans la doc D12.6 (section #6 "Sécurité"), explicitation claire :
- "Holmes MCP filtre automatiquement les credentials de votre installation"
- "Le filtrage suit 3 mécanismes (regex, whitelist, plugins connus) — non garanti exhaustif"
- "Si vous identifiez une fuite, signalez-la immédiatement via [issue GitHub] — patch sous 24h"
- "Holmes MCP n'envoie aucune donnée à des serveurs externes ; les données ne quittent votre box que vers le LLM auquel vous parlez (Claude Desktop, Cursor...) — celui-ci peut conserver les conversations selon ses politiques de confidentialité"

### D15.10 — Sanitisation = trait identitaire produit
🟡 La sanitisation forte est un trait identitaire de Holmes MCP, comme la lecture seule. À mentionner dans :
- Le README market
- L'identité produit (D10.8)
- La doc utilisateur

Formulation type intégrée à l'identité produit : *"Holmes observe, déduit, raconte — sans jamais exposer les secrets de votre maison."*

---

## Tableau récapitulatif des décisions

| # | Titre | Cat. | Statut |
|---|---|---|---|
| D1.1 | Primitives V1 (tools ✅, resources ✅, prompts ❌) | 🟡 | ✅ |
| D1.2 | Version spec MCP cible | 🔵 | ✅ |
| D2.1 | Daemon Python 3.11+ | 🟡 | ✅ |
| D2.2 | Rôle PHP enveloppe market uniquement | 🟡 | ✅ |
| D2.3 | POC J0 daemon Python sur Bookworm | 🟣 | ✅ |
| D2.4 | Cible Bookworm x86_64 + packages.json | 🟡 + 🔵 | ✅ |
| D3.1 | Streamable HTTP | 🟡 | ✅ |
| D3.2 | Binding 0.0.0.0:port/mcp configurable | 🟡 + 🔵 | ✅ |
| D3.3 | URL affichée page config plugin | 🟡 | ✅ |
| D4.1 | Bearer token MCP dédié | 🟡 | ✅ |
| D4.2 | Token par user Jeedom, page config | 🟡 | ✅ |
| D4.3 | HTTP V1, HTTPS = reverse proxy utilisateur | 🟡 | ✅ |
| D4.4 | Scope unique V1 | 🟡 | ✅ |
| D4.5 | Multi-tokens via users Jeedom natifs | 🟡 | ✅ |
| D4.6 | 401 si invalide | 🟡 | ✅ |
| D4.7 | Logs daemon attribués à user Jeedom | 🟡 | ✅ |
| D4bis.1 | Driver MySQL Python + user RO dédié | 🟡 + 🔵 | ✅ |
| D4bis.2 | Création/suppression user MySQL aux hooks | 🟡 + 🔵 | ✅ |
| D4bis.3 | Logs en lecture fichier directe | 🟡 | ✅ |
| D4bis.4 | API JSON-RPC en HTTP localhost | 🟡 | ✅ |
| D4bis.5 | V1 blacklist méthodes modifiantes ; V2+ whitelist | 🟡 | ✅ |
| D4bis.6 | Routage par opération hard-codé | 🟡 | ✅ |
| D4bis.7 | GRANT SELECT à perpétuité, écriture V2+ via API uniquement | 🟡 | ✅ |
| D5.1 | Lecture + assistance V1, écriture V2+ | 🟡 | ✅ |
| D5.2 | Assistance émergente côté LLM | 🟡 | ✅ |
| D5.3 | Liste 25 tools V1 (dont `get_config` ajouté D5.6.bis) | 🟢 | ✅ |
| D5.4 | Tools spécifiques granulaires | 🟡 | ✅ |
| D5.5 | Stabilité contrat V1.x + politique semver explicite | 🟡 | ✅ |
| D5.6 | `query_sql` restreint (blacklist tables sensibles + sanitisation runtime) | 🟡 | ✅ |
| D5.6.bis | Tool dédié `get_config` pour diagnostic standard sur table `config` | 🟡 | ✅ |
| D5.7 | Tools de recherche avancée V1 | 🟡 | ✅ |
| D5.8 | Matrice couverture skill jeedom-audit | 🔵 | ✅ |
| D6.1 | Resources minimales V1 | 🟡 | ✅ |
| D6.2 | Liste 5 resources V1 | 🟢 | ✅ |
| D6.3 | Hybride énumération plafonnée + templates | 🟡 + 🔵 | ✅ |
| D6.4 | Pas de duplication schéma tool↔resource | 🟡 | ✅ |
| D6.5 | Pas de prompts V1 | 🟡 | ✅ |
| D7.1 | Réutilisation par modules de logique | 🟡 | ✅ |
| D7.2 | Organisation `tools/_core/_domain` | 🟡 + 🔵 | ✅ |
| D7.3 | Pas de copie textuelle, adaptation | 🟡 | ✅ |
| D7.4 | Référence permanente aux scripts d'origine | 🟡 | ✅ |
| D8.1 | Scope V1 figé | 🟡 | ✅ |
| D8.2 | Discipline anti-drift | 🟡 | ✅ |
| D8.3 | 9 critères de sortie V1.0.0 | 🟡 | ✅ |
| D8.4 | Bêta privée 2+ semaines, pas de beta-testeurs externes | 🟡 | ✅ |
| D9.1 | Bibliothèques Python complémentaires | 🔵 | ✅ |
| D9.2 | Pas de framework web tiers | 🟡 | ✅ |
| D9.3 | Pas d'ORM | 🟡 | ✅ |
| D9.4 | Pas de table DB interne au plugin | 🟡 | ✅ |
| D10.1 | Structure des fichiers | 🟡 | ✅ |
| D10.2 | Racine repo = racine plugin | 🟡 | ✅ |
| D10.3 | Doc embarquée vs branche `develop` | 🔵 | ✅ |
| D10.4 | AGPL-3.0 + bascule jeedom-skills MIT→AGPL | 🟢 | ✅ |
| D10.5 | Branches `main` + `develop` | 🟡 | ✅ |
| D10.6 | Tags semver + pre-releases jalons | 🟡 | ✅ |
| D10.7 | Pas de submodule jeedom-audit | 🟡 | ✅ |
| D10.8 | Nom et identité du plugin (`holmesMcp` / "Holmes MCP") | 🟢 + 🔵 | ✅ |
| D11.1 | Pyramide unit + intégration + live | 🟡 | ✅ |
| D11.2 | Fixtures synthétiques publiques + réelles privées | 🟡 | ✅ |
| D11.3 | MCP Inspector + client MCP test côté Claude Code | 🟡 | ✅ |
| D11.4 | Tests live exécutés par Claude Code via SSH | 🟡 | ✅ |
| D11.5 | Pas d'évals LLM-side V1 | 🟡 | ✅ |
| D11.6 | CI GitHub Actions minimale | 🟡 + 🔵 | ✅ |
| D11.7 | Cadre d'usage SSH par Claude Code | 🟡 | ✅ |
| D11.8 | Isolation totale credentials du repo | 🟡 | ✅ |
| D12.1 | Market Jeedom voie nominale | 🟡 | ✅ |
| D12.2 | V1.0.0 publié en bêta market | 🟡 | ✅ |
| D12.3 | Jeedom 4.5+, politique N/N-1 | 🟡 | ✅ |
| D12.4 | Semver strict | 🟡 | ✅ |
| D12.5 | Spec MCP N/N-1, breaking = major Holmes | 🟡 | ✅ |
| D12.6 | Doc MkDocs Material sur GitHub Pages, plan 12 sections | 🟡 + 🔵 | ✅ |
| D12.6.bis | Doc = critère sortie V1.0.0 (D8.3 #9) | 🟡 | ✅ |
| D12.7 | Procédure release automatisée Claude Code | 🟡 + 🔵 | ✅ |
| D12.8 | Bugfix 48h critique / semaine majeur | 🟡 | ✅ |
| D12.9 | Maintenance évolutive, ROADMAP.md | 🟡 | ✅ |
| D13.1 | Adoption contrat opérationnel jeedom-skills | 🟡 | ✅ |
| D13.2 | Demandes structurées avec options | 🟡 | ✅ |
| D13.3 | Auto-validation choix triviaux | 🟡 | ✅ |
| D13.4 | Demandes matières physiques explicites et timées | 🟡 | ✅ |
| D13.5 | Sessions courtes orientées avancement | 🟡 | ✅ |
| D13.6 | Routine début de session | 🟡 | ✅ |
| D13.7 | Routine fin de session | 🟡 | ✅ |
| D13.8 | Pas de cadence imposée | 🟡 | ✅ |
| D13.9 | Communication exclusivement en session | 🟡 | ✅ |
| D13.10 | Statut "EN ATTENTE" si goulet bloque | 🟡 | ✅ |
| D14.1 | JSON Lines, schéma standardisé | 🟡 | ✅ |
| D14.2 | Logs Jeedom standards, rotation native | 🟡 | ✅ |
| D14.3 | Niveau `info` par défaut, configurable | 🟡 | ✅ |
| D14.4 | Vue dédiée logs dans page config (tableau filtrable) | 🟡 + 🔵 | ✅ |
| D14.5 | Règles ce qui est/n'est pas loggué | 🟡 | ✅ |
| D14.6 | Erreurs enrichies (type + message PO-friendly) | 🟡 | ✅ |
| D14.7 | Pas de télémétrie externe | 🟡 | ✅ |
| D14.8 | Section diagnostic guidé doc utilisateur | 🟡 | ✅ |
| D14.9 | Logs distincts plugin PHP / daemon Python | 🟡 | ✅ |
| D15.1 | 3 mécanismes cumulés + Mask + count | 🟡 | ✅ |
| D15.2 | Liste regex + hard-codes V1, enrichissement J1 | 🟡 + 🔵 | ✅ |
| D15.3 | Refus `query_sql` ciblant config/champs sensibles | 🟡 | ✅ |
| D15.4 | Sanitisation logs aussi | 🟡 | ✅ |
| D15.5 | Tests 100 % `sanitize.py` + intégration sur fixtures privées | 🟡 | ✅ |
| D15.6 | Sanity check PO à l'œil humain avant V1.0.0 | 🟡 | ✅ |
| D15.7 | Procédure réponse rapide 24h en cas de fuite | 🟡 | ✅ |
| D15.8 | Aucun tool exposant des credentials | 🟡 | ✅ |
| D15.9 | Section sécurité explicite doc utilisateur | 🟡 | ✅ |
| D15.10 | Sanitisation = trait identitaire produit | 🟡 | ✅ |

**Bilan** :
- 🟢 (PO tranche maintenant) : 4 décisions (D5.3, D6.2, D10.4, D10.8)
- 🟡 (Reco modèle validée par PO) : ~85 décisions
- 🔵 (Délégué Claude Code J0/J1 avec critères) : 13 décisions
- 🟣 (POC requis) : 1 décision (D2.3)


---

## Mini-briefs pour les décisions 🔵 (Claude Code J0/J1)

> Cette section consolide les décisions déléguées à Claude Code en J0/J1 sous forme de mini-briefs actionnables. Pour chaque décision, contexte + question + critères + livrable attendu.

### 🔵 D1.2 — Version de la spec MCP cible

**Contexte** : la spec MCP évolue régulièrement (révisions datées : `2024-11-05`, `2025-03-26`, `2025-06-18`, etc.). Cibler une version précise et la figer dans une ADR est non négociable pour pouvoir maintenir le plugin sans casser silencieusement.

**Question à trancher** : quelle version exacte de la spec MCP cibler en V1 ?

**Critères** :
1. Dernière version stable au J0 effectif
2. Compatibilité avec le SDK MCP Python officiel retenu (D2.1, D9.1)
3. Politique de support (typiquement N et N-1, alignée jeedom-skills)
4. Mention claire dans le README V1 pour vérification compat client

**Livrable attendu** : ADR (numéro à attribuer) "Version de la spec MCP cible V1" + mention dans README.

---

### 🔵 D2.4 (partiel) — Mécanisme exact d'isolation Python du daemon

**Contexte** : Jeedom 4.4.9+ gère les venvs Python automatiquement via `packages.json` + `system::getCmdPython3()`. Le pattern exact d'intégration (notamment vis-à-vis de `dependance.lib` de Mips, biblio communautaire alternative) est à confirmer.

**Question à trancher** : utilise-t-on uniquement le mécanisme natif Jeedom 4.4.9+, ou complète-t-on avec `dependance.lib` ?

**Critères** :
1. Adopter `dependance.lib` uniquement si bénéfice clair sans complexifier le diagnostic
2. Liste exacte des paquets `apt` + modules `pip3` requis (dépend du SDK MCP Python ciblé en D1.2 et des bibliothèques D9.1)
3. Politique de version Python min (3.10 vs 3.11) → la plus basse compatible avec le SDK MCP Python officiel cible

**Livrable attendu** : ADR "Stratégie d'installation des dépendances Python" + `plugin_info/packages.json` initial.

---

### 🔵 D3.2 (partiel) — Port par défaut + path de l'endpoint MCP

**Contexte** : pas de mécanisme Jeedom pour éviter les collisions de ports entre plugins. Convention : choisir un port haut, libre des plugins majeurs, le rendre configurable.

**Question à trancher** : quel port par défaut + quel path d'endpoint MCP ?

**Critères** :
1. Port haut (>8000), **non utilisé par les plugins Jeedom majeurs** (vérifier au minimum : MQTT Manager, jMQTT, MP_Server, Mobile, Z-Wave JS UI, Zigbee2MQTT, et tout autre plugin observé sur la box du PO)
2. Path : aligner sur la convention par défaut du SDK MCP Python officiel cible

**Livrable attendu** : ADR "Port et path d'écoute du daemon MCP" + valeur par défaut dans `core/config/holmesMcp.json` ou équivalent + champ configurable dans la page de config.

---

### 🔵 D4bis.1 (partiel) — Choix du driver MySQL Python

**Contexte** : driver MySQL Python à choisir entre PyMySQL et mysql-connector-python (et autres alternatives éventuelles).

**Question à trancher** : quel driver retenir ?

**Critères** :
1. Pure Python (pas de deps C compilées) si possible
2. Maintenance active (commits dans les 12 derniers mois)
3. Support Python 3.11+ confirmé
4. Compatible MySQL 5.7 + MariaDB 10.x (versions Jeedom)
5. **Reco par défaut : PyMySQL** sauf raison forte

**Livrable attendu** : ADR "Choix du driver MySQL Python" + ligne dans `packages.json` (section pip3).

---

### 🔵 D4bis.2 (partiel) — Mécanisme d'obtention des creds Jeedom et création user RO

**Contexte** : le plugin doit créer un user MySQL `jeedom_mcp_ro` à l'install. Ça nécessite d'avoir les creds du user Jeedom principal (qui doit avoir `CREATE USER` privilege).

**Question à trancher** : comment lire les creds Jeedom de manière fiable et gérer le cas où `CREATE USER` n'est pas disponible ?

**Critères** :
1. Lire `core/config/common.config.php` côté PHP pour récupérer les creds Jeedom (lecture seule)
2. Tester si la création de user fonctionne (le user Jeedom standard a-t-il `CREATE USER` privilege ?)
3. Si pas de privilege CREATE USER → message clair à l'utilisateur (rare mais existe selon types d'install)
4. Documenter en ADR le mécanisme retenu

**Livrable attendu** : ADR "Création du user MySQL read-only à l'install" + code dans `plugin_info/install.php` (`holmesMcp_install()`).

---

### 🔵 D5.8 — Matrice de couverture fonctionnelle skill jeedom-audit

**Contexte** : le couplage acté à terme jeedom-audit ↔ Holmes MCP (D5.8) impose que le périmètre V1 du MCP couvre l'ensemble des cas d'usage des scripts actuels de jeedom-audit. Sinon, la bascule future de la skill consommatrice MCP perdra des capacités.

**Question à trancher** : la liste de 25 tools D5.3 couvre-t-elle l'ensemble des workflows WF1-WF13 de jeedom-audit ? Si non, quels ajouts ou différés en V1.x ?

**Critères** :
1. Lire le SKILL.md de jeedom-audit + les références (`audit-templates.md`, `sql-cookbook.md`) pour identifier les WF1-WF13
2. Mapper chaque workflow aux tools MCP V1
3. Pour les workflows non couverts : ADR avec arbitrage (différer V1.x ou ajouter un tool V1)
4. Référencer les commits/tags précis de jeedom-audit (pas de submodule)
5. Soumettre les ajouts/retraits éventuels au PO pour validation

**Livrable attendu** : `docs/skill-coverage-matrix.md` + ADR "Couverture des workflows skill jeedom-audit" + éventuels ajouts à D5.3 validés par PO.

---

### 🔵 D6.3 (partiel) — Plafond de l'énumération des resources

**Contexte** : l'approche hybride D6.3 (énumération plafonnée + templates) nécessite de fixer un plafond N pour les scénarios et équipements énumérés dans `resources/list`.

**Question à trancher** : quelle valeur N pour le plafond d'énumération par catégorie ?

**Critères** :
1. Claude Desktop reste réactif (pas de freeze à l'ouverture du picker resources)
2. Lisibilité de la liste (pas trop long à scroller)
3. Mesure empirique sur la box du PO (Claude Code peut tester via SSH)

**Livrable attendu** : ADR "Plafond de l'énumération des resources MCP" + valeur dans le code daemon.

---

### 🔵 D7.2 (partiel) — Détails de découpage interne du daemon

**Contexte** : la structure stratifiée `tools/`, `resources/`, `_core/`, `_domain/`, `jeedom/` est posée (D7.2). Les détails de nommage et de découpage interne (un fichier par tool ? un fichier par famille ?) sont à arbitrer.

**Question à trancher** : granularité fine des modules.

**Critères** :
1. Lisibilité (un développeur extérieur peut naviguer sans aide)
2. Cohérence avec les conventions Python standards
3. Auto-validation D13.3 — pas de blocage PO sur ce niveau de détail

**Livrable attendu** : structure finale `resources/holmesMcpd/` validée et stable dès J3.

---

### 🔵 D9.1 — Bibliothèques Python complémentaires

**Contexte** : au-delà du SDK MCP officiel et du driver MySQL, le daemon a besoin de bibliothèques pour HTTP localhost, parsing SQL, logs structurés, tests.

**Question à trancher** : choix précis de chaque biblio.

**Critères** :
1. Bibliothèques **standards et matures** (PyPI top 1000, maintenance active)
2. Minimiser le nombre de dépendances tierces
3. Toutes les deps déclarables proprement dans `packages.json` (section `pip3`)
4. Documenter en ADR le choix final et les versions épinglées

**Reco par défaut** :
- HTTP : `httpx` si daemon async, `requests` sinon
- Parsing SQL : `sqlparse` (éprouvé) ou parser custom léger si SELECT-only suffit
- Logs : `structlog` recommandé pour D15 si pas de friction install ; sinon `logging` stdlib avec formatter JSON

**Livrable attendu** : ADR "Choix des bibliothèques Python complémentaires" + `requirements.txt` de référence + section `pip3` dans `packages.json`.

---

### 🔵 D10.3 — Doc projet (`docs/`) embarquée vs branche séparée

**Contexte** : la racine du repo est la racine du plugin Jeedom (D10.2), donc `docs/` est embarqué dans l'install utilisateur. Acceptable ou pollution ?

**Question à trancher** : tout sur `main`, ou `main` propre + `develop` portant `docs/` ?

**Critères** :
1. Si `docs/` embarqué pose un problème de poids ou de propreté market → branche `develop` pour la doc, `main` propre
2. Sinon (cas par défaut) → tout dans `main`, plus simple à maintenir
3. À arbitrer après vérification du processus de packaging market réel
4. Documenter en ADR

**Livrable attendu** : ADR "Stratégie de séparation doc/code" + structure de branche définitive.

---

### 🔵 D11.6 (partiel) — Outils lint/format Python

**Contexte** : CI GitHub Actions minimale + lint Python.

**Question à trancher** : `ruff`, `flake8`, `black`, `isort`, ou combinaison ?

**Critères** :
1. Standard 2026, maintenance active
2. Rapide en CI
3. Documenter en ADR

**Reco par défaut : `ruff`** (lint + format unifié, très rapide, état de l'art 2025-2026).

**Livrable attendu** : ADR "Outils lint/format Python" + config dans `pyproject.toml`.

---

### 🔵 D12.6 (partiel) — Setup MkDocs et CI doc

**Contexte** : doc utilisateur sur GitHub Pages avec MkDocs Material (D12.6).

**Question à trancher** : configuration exacte MkDocs + workflow GitHub Actions de publication.

**Critères** :
1. Setup MkDocs Material avec navigation, sélecteur de version, recherche, dark mode
2. CI GitHub Actions qui rebuild la doc à chaque push sur `main` et publie sur `gh-pages`
3. Validation que l'URL `gh-pages` est accessible avant le premier renseignement de `info.json`
4. ADR du choix de stack doc

**Livrable attendu** : `mkdocs.yml` + `.github/workflows/docs.yml` + URL `gh-pages` opérationnelle + ADR "Stack doc utilisateur" + valeurs `documentation` / `documentation_beta` dans `info.json`.

---

### 🔵 D12.7 (partiel) — Procédure de soumission market automatisable ?

**Contexte** : la procédure de release est largement automatisable côté Claude Code. La soumission market Jeedom finale peut être manuelle ou via API/UI développeur Jeedom selon ce qui est disponible.

**Question à trancher** : étapes manuelles vs automatisables.

**Critères** :
1. Vérifier ce que permet l'API/UI développeur Jeedom à ce moment
2. Lister explicitement les étapes manuelles (PO) vs automatisées (Claude Code)
3. Documenter en ADR

**Livrable attendu** : ADR "Procédure de release et soumission market" + script/checklist `.github/release.md` ou équivalent.

---

### 🔵 D14.4 (partiel) — Détails UI vue dédiée logs

**Contexte** : vue dédiée logs Holmes MCP dans la page de config plugin (tableau filtrable).

**Question à trancher** : framework JS, refresh auto, filtres exacts.

**Critères** :
1. La vue doit fonctionner dans l'UI Jeedom standard sans dépendance JS exotique
2. Filtres : par utilisateur, par tool, par niveau, par fenêtre temporelle (dernière heure / jour / 7 jours)
3. Refresh automatique configurable (5s, 30s, off)
4. Accessibilité PO non-dev

**Livrable attendu** : code `desktop/php/holmesMcp.php` + `desktop/js/holmesMcp.js` + tests visuels validés via SSH par Claude Code.

---

### 🔵 D15.2 (partiel) — Liste hard-codée des plugins à filtrer

**Contexte** : liste initiale de plugins hard-codés au minimum V1 (jMQTT, Aqara, Tuya, Hue, Telegram, OpenWeatherMap, MQTT Manager, Mobile). À enrichir.

**Question à trancher** : liste complète V1 par revue des 10 plugins les plus installés.

**Critères** :
1. Lecture des README/sources des 10 plugins Jeedom les plus installés (statistique market)
2. Identification des clés `configuration` qui contiennent des credentials
3. Ajout à la liste hard-codée
4. ADR de la liste V1.0.0 + procédure de mise à jour communautaire (issues GitHub)

**Livrable attendu** : `_domain/sanitize.py` enrichi + ADR "Liste de plugins hard-codés pour sanitisation V1" + template d'issue GitHub "Champ sensible non filtré".

---

### 🔵 D10.8 (partiel) — Vérification disponibilité ID `holmesMcp` + collision marque

**Contexte** : le PO a choisi `holmesMcp` / "Holmes MCP" comme nom et ID (D10.8). À vérifier avant figeage.

**Question à trancher** : `holmesMcp` est-il libre comme ID Jeedom market ? Pas de collision marque évidente ?

**Critères** :
1. Vérifier que `holmesMcp` est libre comme ID Jeedom market (recherche market officielle)
2. Vérifier qu'il n'y a pas de collision marque évidente sur l'écosystème domotique francophone
3. Si conflit identifié → escalade au PO avec alternatives (`jeedoscope`, `vigieMcp`, `holmesMcpAudit`, autre)

**Livrable attendu** : confirmation écrite (commentaire ADR ou entrée session) que l'ID est libre + go pour usage du nom.

---

## POCs requis avant validation (🟣)

> Cette section consolide les décisions nécessitant un POC avant figeage du PLANNING. Elles doivent être conduites en **J0**, idéalement comme premier jalon, **avant** que Claude Code n'engage la suite de l'implémentation.

### 🟣 D2.3 — POC J0 "Faisabilité daemon Python sur Bookworm"

**Contexte** : l'architecture "plugin PHP minimaliste + daemon Python lancé par hooks Jeedom standards" est un pattern documenté par Jeedom (jMQTT, Mobile, etc.) et adopté ici. **Cependant**, la combinaison spécifique (SDK MCP Python officiel + venv Bookworm + intégration `deamon_*` Jeedom + serveur HTTP MCP exposé) n'a pas été éprouvée dans le contexte précis du PO. Un POC borné est nécessaire avant d'engager la construction complète.

**Hypothèses à valider** :
1. Le SDK MCP Python officiel s'installe proprement dans un **venv** géré via `packages.json` (méthode moderne Jeedom 4.4.9+) sur Debian 12 Bookworm x86_64
2. `system::getCmdPython3(__CLASS__)` retourne le Python du venv après installation des deps
3. Un daemon Python "hello world MCP" est lancé/arrêté correctement par les hooks `deamon_start()` / `deamon_stop()` côté PHP
4. Le pidfile est correctement écrit, `deamon_info()` retourne l'état approprié
5. L'état du daemon (vert/rouge) s'affiche correctement dans le cadre "Démon" UI plugin standard Jeedom
6. Un client MCP externe (MCP Inspector) qui se connecte au port HTTP MCP exposé reçoit la liste de tools déclarés (au moins un tool fictif `hello`) via `tools/list`
7. **Connexion réelle Claude Desktop sur la machine PO** vers l'URL HTTP du daemon en LAN (`http://<ip-jeedom>:<port>/mcp` + Bearer token), avec `tools/list` opérationnel et invocation du tool `hello` qui retourne sa réponse. Goulet PO physique (Claude Code n'a pas accès à la machine PO).

**Protocole de test minimal** :
1. Créer un plugin "shell" minimal `holmesMcpPoc` (à partir du plugin template officiel) sur la box du PO via SSH
2. Implémenter `info.json` avec `hasOwnDeamon: true` + `hasDependency: true` + `packages.json` listant le SDK MCP Python officiel
3. Implémenter les méthodes `deamon_*` PHP minimales
4. Implémenter un daemon Python `holmesMcpPocd.py` qui :
   - Lit le template Jeedom (`jeedom_socket`, `jeedom_com`, `jeedom_utils`)
   - Lance un serveur MCP Streamable HTTP avec un seul tool fictif `hello` qui retourne `{"message": "Hello from Holmes MCP POC"}`
5. Installer le plugin via le mécanisme Jeedom standard (depuis sources, pas via market évidemment)
6. Démarrer le daemon via l'UI Jeedom
7. Connecter MCP Inspector (côté machine de dev Claude Code) au port exposé, vérifier `tools/list` et l'invocation de `hello`
8. **Demander au PO d'ajouter le serveur MCP dans son Claude Desktop (URL + Bearer token), vérifier la connexion + `tools/list` + invocation `hello`. PO partage retour (succès/échec/captures).**
9. Arrêter le daemon, vérifier que le pidfile est nettoyé

**Critère de succès** : les 7 hypothèses validées. Le plugin "shell" est installable via mécanisme Jeedom standard, démarre/arrête proprement, est observable dans l'UI Jeedom, et répond à la fois à MCP Inspector ET à Claude Desktop sur la machine du PO.

**Critère d'échec** : impossibilité sur l'une des 7 hypothèses malgré 2-3 jours de recherche (équivalent ~3-4 sessions Claude Code).

**Plan B si échec** :
- **Si problème SDK Python sur Bookworm via venv** → escalade PHP (Option B de l'ADR-0019), assumer dette SDK communautaire (notamment `php-mcp/server` ou `logiscape/mcp-sdk-php`). Réécriture significative requise.
- **Si problème intégration daemon Jeedom** → garder Python mais lancer via systemd externe au lieu des hooks Jeedom natifs (perte UX market mais faisable). Pas d'état dans l'UI plugin standard, gestion manuelle du cycle de vie.
- **Si problème spécifique au pattern packages.json/venv** → fallback méthode `dependancy_install()` + script shell adapté Bookworm (méthode legacy, plus de friction d'install).
- **Si problème connexion Claude Desktop HTTP non-TLS en LAN (hypothèse 7)** → activation du **plan B HTTPS self-signed** : génération auto certif `openssl` dans `holmesMcp_install()` PHP, exposition daemon Python en HTTPS, instructions doc pour ajout du certif aux trust stores. Coût +1 à 2 jours d'implémentation. ADR documentant le passage HTTP → HTTPS self-signed.
- Documenter en ADR le problème rencontré et l'arbitrage retenu.

**Livrable attendu** : un POC fonctionnel committé sur une branche dédiée (à supprimer après) ou archivé dans `docs/poc/`, ADR de validation/invalidation des hypothèses, et **go/no-go formel** pour engager la suite du PLANNING tel que tranché dans ce brief.

---

## Risques techniques identifiés

> Cette section ne contient PAS de décisions ouvertes (toutes sont tranchées dans la section principale). Elle documente les risques résiduels que Claude Code et le PO devront surveiller en exécution.

### 10.1 Risques liés au POC J0 (D2.3)

- **Indisponibilité du SDK MCP Python officiel** sur Python 3.10/3.11 dans certaines configurations Bookworm exotiques. Mitigation : test précoce, plans B documentés (D2.3).
- **Incompatibilité venv Jeedom 4.4.9+** sur certaines installs spécifiques. Mitigation : fallback méthode legacy `dependancy_install()`.
- **Conflit de port** avec un autre plugin sur la box du PO. Mitigation : configurabilité du port (D3.2), revue des ports utilisés en J0.

### 10.2 Risques liés à la sanitisation (D16)

- **Plugins exotiques avec nommage non-standard** dont les credentials passent à travers les 3 mécanismes. Mitigation : sanity check PO à l'œil humain avant V1.0.0 (D15.6) + procédure réponse rapide 24h en cas de fuite (D15.7) + enrichissement communautaire de la liste hard-codée (D15.2).
- **Champs sensibles dans des emplacements imprévus** (ex. valeurs `dataStore` contenant des creds en clair). Mitigation : regex large + tests d'intégration sur fixtures réelles (D15.5).
- **Prompt injection ciblée** demandant explicitement les credentials. Mitigation : refus explicite côté daemon (D15.3 pour `query_sql`) + masquage actif systématique (D15.1).

### 10.3 Risques liés à la spec MCP

- **Évolutions breaking de la spec MCP** entre V1 et V1.x. Mitigation : politique support N et N-1 (D12.5), figeage de la version cible en ADR (D1.2).
- **Support hétérogène entre clients MCP** (Claude Desktop bien, Cursor moins, n8n variable, etc.). Mitigation : tests sur Claude Desktop + un autre client minimum avant V1.0.0 (D8.3 #4).
- **Streamable HTTP encore récent dans certains SDKs** : risque de bugs en SDK Python. Mitigation : tests d'intégration approfondis, fallback HTTP+SSE déprécié si vraiment bloquant (à évaluer en J0).
- **Claude Desktop pointilleux sur les connexions HTTP non-TLS, même en LAN** : risque de blocage silencieux des requêtes pre-flight ou refus de connexion sans HTTPS, indépendamment de la qualité du serveur Python. Mitigation : 5e point du POC J0 (D2.3 hypothèse 7) qui valide cette connexion en conditions réelles sur la machine PO ; plan B HTTPS self-signed activé sans hésitation si le test échoue.

### 10.4 Risques liés à l'écosystème Jeedom

- **Validateur market Jeedom** : critères pas entièrement publics, risque de refus à la première soumission (icône, structure, etc.). Mitigation : revue des critères en J0/J7 par lecture de la doc soumission, pre-submit checklist.
- **Évolution du core Jeedom** (4.6, 4.7, ...) : changements de schéma DB ou d'API. Mitigation : politique N/N-1 (D12.3), ADR à chaque évolution majeure.
### 10.5 Risques liés au binôme PO non-dev / Claude Code

- **Validation PO en goulot d'étranglement sur captures et soumission market**. Mitigation : demandes structurées, timées, groupées (D13.4) + auto-validation des choix triviaux (D13.3).
- **Drift de compréhension entre sessions espacées**. Mitigation : discipline `PROJECT_STATE.md` + sessions/ (D13.6, D13.7) + relecture explicite si > 2 semaines (D13.8).
- **Dérive de scope** : tentation d'ajouter "juste cette petite feature" en cours de V1. Mitigation : discipline anti-drift D8.2.

### 10.6 Risques liés à la sphère jeedom-audit ↔ Holmes MCP

- **Couplage juridique licence** si bascule jeedom-skills MIT→AGPL incomplète. Mitigation : vérification J0 que le PO est seul copyright holder (D10.4).
- **Désynchronisation** entre la skill et le MCP avant la bascule officielle. Mitigation : matrice de couverture D5.8, références par commits/tags précis (D10.7).
- **Casse de la skill** si breaking change MCP non communiqué. Mitigation : politique semver stricte (D5.5), `holmesMcp >= 1.0, < 2.0` côté skill.

### 10.7 Risques liés à la sécurité

- **Fuite de credentials via le repo** (commit accidentel d'IP, token, hostname...). Mitigation : .gitignore strict, pre-commit/pre-push hooks de scan, review systématique PR (D11.8).
- **Token MCP compromis** d'un utilisateur Jeedom. Mitigation : régénération individuelle disponible (D4.2), logs de chaque requête attribués à un user (D4.7) permettant détection.
- **Exposition hors LAN sans HTTPS** par un utilisateur imprudent. Mitigation : doc explicite (D4.3, D12.6 section sécurité), avertissement dans la page de config plugin si IP non-LAN détectée (à arbitrer en exécution).

### 10.8 Risques liés à la maintenance long terme

- **PO unique mainteneur initial** : risque d'abandon ou d'indisponibilité. Mitigation : doc rigoureuse, ADRs traçables, code commenté ; possibilité de transmission communautaire si nécessaire (D10.4 AGPL favorise les forks open source).
- **Évolutions rapides de l'écosystème MCP** : risque que Holmes MCP devienne obsolète. Mitigation : ADR à chaque évolution majeure de la spec.


---

## Liste des artefacts attendus du PLANNING.md

> **Distinction importante** : ce brief de cadrage **n'est pas** le `PLANNING.md` du projet. Cette section guide la **production** du `PLANNING.md` par Claude Code en sortie de session de planning, mais elle n'**est pas** une partie du `PLANNING.md` lui-même. Le brief reste figé dans `docs/sources/00-brief-cadrage.md` ; le `PLANNING.md` vivant et opérationnel est un document distinct, à produire en sortie de session.
>
> Cette section est une **amorce** (1 page max), pas un PLANNING complet. L'objectif est de donner à Claude Code en mode plan une direction structurelle pour la production du `docs/PLANNING.md`. **Claude Code en mode plan reste libre de structurer le PLANNING comme il le juge approprié**, à condition de couvrir au minimum les éléments listés ci-dessous.

### Structure du PLANNING.md attendue

1. **Introduction et contexte** (référence au brief de cadrage `docs/sources/00-brief-cadrage.md`, rappel identité produit Holmes MCP)
2. **Modèle opérationnel PO / Claude Code** (reprise section 0 du brief, ou référence)
3. **Architecture cible** (synthèse stack, schéma plugin/daemon, canaux d'accès)
4. **Périmètre V1** (rappel D8.1 + critères de sortie D8.3 + bêta privée D8.4)
5. **Jalons J0-Jn** (à structurer par Claude Code en mode plan)
6. **Roadmap V1.x / V2+** (mention candidates)
7. **ADRs initiales pressenties**
8. **Annexe glossaire** (Jeedom, MCP, sphère)

### Jalons J0-Jn pressentis

> Ordre de grandeur indicatif basé sur le retour d'expérience jeedom-skills (~7 jalons J0-J7). À raffiner par Claude Code en mode plan.

| Jalon | Objectif principal | Durée indicative | Inclut |
|---|---|---|---|
| **J0** | Bootstrap + POC | 2-3 sessions | Bootstrap repo (structure, ADRs initiales, contrat opérationnel, PROJECT_STATE.md), POC D2.3 (🟣 critique), vérification ID `holmesMcp` D10.8, bascule licence jeedom-skills MIT→AGPL conjointe (D10.4) |
| **J1** | Couche `_core` + matrice couverture skill | 3-4 sessions | Implémentation `_core/` (auth, db, api, logs), tests unitaires, matrice de couverture D5.8 livrée, ADR de mapping skill |
| **J2** | Couche `_domain` + sanitiseur | 2-3 sessions | Implémentation `_domain/` (usage_graph, scenario_walker, cmd_refs, sanitize), tests unitaires 100% sanitize.py, fixtures synthétiques |
| **J3-J4** | Tools de base | 4-5 sessions | Implémentation des tools "découverte d'install", "équipements/commandes", "scénarios" (16 tools sur 24), tests intégration |
| **J5** | Tools transverses + resources + `query_sql` | 2-3 sessions | Implémentation tools "variables", "logs/diagnostic", "recherche", `query_sql` restreint, 5 resources, tests intégration |
| **J6** | Vue UI logs + observabilité + durcissement | 2-3 sessions | Vue dédiée logs Holmes MCP (D14.4), enrichissement listes sanitisation D15.2, sanity check sanitisation par PO sur sa box (D15.6) |
| **J7** | Doc + identité produit + bêta privée | 1-2 sessions + bêta privée 2+ semaines | Documentation utilisateur MkDocs (D12.6), README market-friendly, identité produit, captures PO, bêta privée sur box PO (D8.4), soumission market en bêta |

**Total estimé : ~15-20 sessions Claude Code + 2+ semaines bêta privée**.

### ADRs initiales pressenties (à rédiger en J0 par Claude Code à partir de ce brief)

À soumettre par lots de 3-5 au PO pour validation, pas d'un coup.

1. **ADR-0001** : Architecture Holmes MCP (synthèse — plugin PHP + daemon Python, transport Streamable HTTP)
2. **ADR-0002** : Stack technologique (D2.1, D9.1)
3. **ADR-0003** : Version de la spec MCP cible V1 (D1.2)
4. **ADR-0004** : Authentification MCP externe (Bearer token par user Jeedom — D4.x)
5. **ADR-0005** : Canaux d'accès aux données Jeedom (D4bis.x)
6. **ADR-0006** : Périmètre fonctionnel V1 et roadmap V2+ (D5.1, D8.1)
7. **ADR-0007** : Liste des tools V1 (D5.3)
8. **ADR-0008** : Liste des resources V1 (D6.2)
9. **ADR-0009** : Réutilisation des scripts jeedom-audit (D7.x)
10. **ADR-0010** : Nom et identité produit Holmes MCP (D10.8, D10.4)
11. **ADR-0011** : Licence AGPL-3.0 + bascule jeedom-skills (D10.4)
12. **ADR-0012** : Stratégie de tests (D12.x)
13. **ADR-0013** : Sécurité opérationnelle — isolation des credentials (D11.8)
14. **ADR-0014** : Distribution market et politique de versioning (D13.x)
15. **ADR-0015** : Modèle opérationnel PO / Claude Code (D14.x, section 0)
16. **ADR-0016** : Observabilité (D15.x)
17. **ADR-0017** : Sanitisation et guardrails (D16.x)
18. **ADR-0018** : Résultat du POC J0 D2.3 (à rédiger après POC)
19. **ADR-0019** : Couverture fonctionnelle skill jeedom-audit (à rédiger après J1, suite à D5.8)

### Livrables PO et livrables Claude Code attendus à chaque jalon

> Synthèse — à raffiner par Claude Code en mode plan.

**Livrables PO** (matières physiques + validations) :
- **J0** : confirmation copyright holder jeedom-skills, validation ID `holmesMcp`, validation reco POC, sortie POC validée, validation contrat opérationnel
- **J1-J6** : validations de blocs de code livrés, validation matrice couverture (J1), validation listes sanitisation (J6)
- **J7** : captures d'écran UI Jeedom (3-5 captures), validation Claude Desktop sur sa machine, sanity check sanitisation, validation doc utilisateur, soumission market, annonce forum

**Livrables Claude Code** (production complète sauf matières physiques) :
- **J0** : structure repo, ADRs initiales, POC fonctionnel, PROJECT_STATE.md, CONTRIBUTING-CLAUDE-CODE.md
- **J1-J6** : code (couches `_core`, `_domain`, `tools`, `resources`), tests, fixtures synthétiques, vue UI logs, ADRs en cours
- **J7** : doc MkDocs complète, README, build packagé, scripts de release, communication forum (rédigée, soumise PO pour validation)

---

## Annexe — Glossaire

> Pour Claude Code en planification.

- **MCP** : Model Context Protocol, protocole standard Anthropic ouvert basé JSON-RPC 2.0, permettant à un client LLM (Claude Desktop, Cursor, n8n, etc.) de découvrir et invoquer des outils/données exposés par un serveur tiers
- **Tool MCP** : fonction appelable, verbe paramétré, le LLM décide de l'appeler
- **Resource MCP** : URI attachable par l'utilisateur dans son client (Claude Desktop), donnée navigable
- **Prompt MCP** : slash command exposé par le serveur (hors V1)
- **Streamable HTTP** : transport HTTP de la spec MCP 2025-03-26+ (anciennement HTTP+SSE déprécié)
- **Plugin Jeedom** : assemblage `info.json` + classe PHP + vues + optionnellement daemon, distribuable via le Market Jeedom officiel
- **Daemon (Jeedom)** : processus permanent lancé/arrêté par hooks `deamon_*` (graphie officielle avec faute, conservée par le core)
- **eqLogic** : équipement Jeedom, table `eqLogic`, porte un `eqType_name` qui désigne le plugin owner
- **cmd** : commande Jeedom, table `cmd`. Type info (lecture) ou action (écriture). Attachée à un eqLogic
- **scenarioElement** : nœud d'un scénario (table `scenarioElement`), hiérarchie via `parentId`
- **scenarioSubElement** : sous-nœud (THEN, ELSE, condition...), table `scenarioSubElement`
- **scenarioExpression** : feuille (condition ou action), table `scenarioExpression`
- **dataStore** : variables persistantes (table `dataStore`)
- **history / historyArch** : tables d'historisation des cmd info
- **`#[O][E][C]#`** : convention de nommage `#[Objet][Équipement][Commande]#`, forme humaine de `#cmdId#`
- **logicalId** : champ d'identification logique, conventions plugin-spécifiques (jMQTT porte le topic, etc.)
- **Type Générique** : classification orthogonale des cmd (Lumière, Volet, Thermostat...)
- **`packages.json`** : fichier de déclaration moderne des dépendances plugin (Jeedom 4.2+) — sections `apt`, `pip3`, etc.
- **Spec MCP** : spécification du Model Context Protocol par Anthropic, révisions datées
- **MCP Inspector** : outil officiel Anthropic permettant de connecter à un serveur MCP et tester `tools/list`, invocations, etc.
- **Sphère jeedom-audit** : ensemble cohérent jeedom-audit (skill Claude Code) + Holmes MCP (plugin Jeedom), couplés à terme par bascule de la skill consommatrice MCP
- **PO** : Product Owner — utilisateur humain décideur
- **Claude Code (CC)** : implémenteur — rédige et code, pose des questions structurées au PO
- **ADR** : Architecture Decision Record. Fichier markdown dans `docs/decisions/` documentant une décision structurante
- **Bêta privée** : phase de test sur la seule box du PO avant soumission market (D8.4)
- **Bêta market** : statut de release sur le market Jeedom avant conversion stable (D12.2)

---

*Fin du brief de cadrage. Document rédigé en sortie d'une session d'idéation collaborative, ~108 décisions consolidées (D1.1 à D15.10) + modèle opérationnel PO/Claude Code (section 0). À ingérer en mode planification dans un nouveau repo Claude Code vide nommé `holmesMcp` (à créer par le PO sur GitHub avant la première session Claude Code de J0).*
