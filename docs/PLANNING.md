# PLANNING.md — Holmes MCP

> Document vivant — produit en sortie de la session de planning 2026-05-03.  
> Source d'autorité figée : `docs/sources/00-brief-cadrage.md`.  
> Toute évolution des décisions du brief passe par ADR dans `docs/decisions/`.

---

## 1. Introduction et contexte

**Holmes MCP** est un plugin Jeedom natif open source (AGPL-3.0) qui expose la box Jeedom comme serveur MCP (Model Context Protocol) à n'importe quel client compatible — Claude Desktop, Cursor, MCP Inspector, n8n et autres. Il s'inscrit dans la **sphère jeedom-audit** : projet séparé de `jeedom-skills` (ADR-0020 accepted), avec un couplage acté à terme — la skill jeedom-audit basculera dans une version future en consommatrice exclusive de Holmes MCP pour ses accès aux données Jeedom.

**Identité produit** : *Holmes observe, déduit, raconte — sans jamais toucher à la scène, sans jamais exposer les secrets de votre maison.* Lecture seule V1, sanitisation forte des credentials, garantie technique read-only au niveau base de données.

**Cible utilisateur** : Jeedomistes éclairés équipés d'un client MCP (Claude Desktop, Cursor…) qui veulent interagir avec leur installation domotique en langage naturel, **sans setup technique côté client** — juste une URL et un token à coller dans leur client MCP.

**Cible OS V1** : Debian 12 Bookworm x86_64 + Jeedom 4.5+. Bullseye, ARM/Pi, autres : best-effort non testé V1.

**Posture de conception** : **clean room** — fondée uniquement sur les scripts jeedom-audit existants, la documentation Jeedom officielle, la spécification MCP officielle Anthropic, et les décisions du brief. Aucune référence à d'autres plugins MCP Jeedom.

---

## 2. Modèle opérationnel PO / Claude Code

Binôme PO (décideur, non-développeur) / Claude Code (implémenteur). Détail complet dans `docs/state/CONTRIBUTING-CLAUDE-CODE.md`. Résumé :

- **PO** : décide, valide, fournit les 6 matières physiques non-délégables (captures UI, validation Claude Desktop, sanity check sanitisation, soumission market, forum, snapshots Proxmox)
- **Claude Code** : rédige tout texte/code, exécute via SSH (alias `Jeedom`, user `jeedom`, blacklist commandes), propose des arbitrages structurés (2-4 options + reco), auto-valide les triviaux
- **Continuité** : `docs/state/PROJECT_STATE.md` + `docs/sessions/` mis à jour à chaque session significative

---

## 3. Architecture cible

```
┌────────────────────────────────────────────────────┐
│   Claude Desktop / Cursor / MCP Inspector          │
│   (n'importe quel client MCP compatible)           │
└────────────────────┬───────────────────────────────┘
                     │ Streamable HTTP (Bearer token)
                     │ http://<ip-jeedom>:<port>/mcp
                     ▼
┌────────────────────────────────────────────────────┐
│  PLUGIN JEEDOM — holmesMcp                         │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  holmesMcp.class.php (enveloppe PHP)         │  │
│  │  • info.json (hasOwnDeamon, hasDependency)   │  │
│  │  • deamon_start() / deamon_stop() / info()   │  │
│  │  • Page config UI : token/user, port, logs   │  │
│  │  • Callback jeeholmesMcp.php                 │  │
│  └────────────────────┬─────────────────────────┘  │
│                       │ fork + pidfile              │
│  ┌────────────────────▼─────────────────────────┐  │
│  │  holmesMcpd.py  (daemon Python 3.11+)        │  │
│  │  + SDK MCP officiel Anthropic                │  │
│  │  + 25 tools en 6 familles                   │  │
│  │  + 5 resources minimales                    │  │
│  │  + auth Bearer par user Jeedom               │  │
│  │  + sanitisation 3 mécanismes cumulés         │  │
│  │  + logs JSON Lines holmesMcp_daemon          │  │
│  └──────┬──────────────┬────────────────┬───────┘  │
│         │              │                │          │
│    MySQL (RO)     Fichiers logs     API JSON-RPC   │
│  user jeedom_    Jeedom (lecture    localhost       │
│  mcp_ro (SELECT  directe fichiers)  /core/api/     │
│  uniquement)                        jeeApi.php     │
│                                                    │
└────────────────────────────────────────────────────┘
           Jeedom 4.5+ / Debian 12 Bookworm x86_64
```

**Canaux d'accès aux données Jeedom** (routage hard-codé D4bis.6) :

| Opération | Canal |
|---|---|
| Audit structurel (jointures, scénarios, équipements, commandes, plugins) | MySQL RO |
| État runtime (`lastLaunch`, `state`, `currentValue`) | API JSON-RPC |
| Historique récent | API JSON-RPC |
| Historique archivé | MySQL (`historyArch`) |
| Logs Jeedom | Lecture fichier local |
| Écriture (V2+) | API JSON-RPC uniquement, **jamais SQL** |

---

## 4. Périmètre V1

### 4.1 Scope V1 figé (D8.1)

**Inclus V1** :
- Plugin Jeedom natif (PHP + daemon Python), Streamable HTTP
- Auth Bearer par user Jeedom
- 3 canaux d'accès données (MySQL RO + logs fichier + API JSON-RPC localhost)
- **25 tools** en 6 familles (lecture + `query_sql` restreint + `get_config` dédié)
- **5 resources** minimales
- Sanitisation forte (3 mécanismes cumulés — whitelist + regex + hard-code plugins)
- Matrice de couverture skill jeedom-audit (D5.8)
- Documentation utilisateur MkDocs Material sur GitHub Pages
- Identité produit Holmes MCP
- Cible OS Debian 12 Bookworm x86_64 + Jeedom 4.5+

**Hors V1 — discipline anti-drift (D8.2)** : aucune feature non tranchée dans le brief. Tout nouveau besoin → ROADMAP.md. Si bloquant pour V1 → ADR + validation PO explicite avant ajout.

### 4.2 Politique semver (D5.5)

| Version | Portée |
|---|---|
| `1.0.x` | Patches (corrections, perfs, descriptions enrichies) — schémas tools/resources **inchangés** |
| `1.x.0` | Minor (nouveaux tools, paramètres optionnels rétro-compatibles) |
| `2.0.0` | Major (breaking changes possibles, migration guide) |

Pré-releases jalons internes : `v0.1.0`, `v0.2.0`, etc.

### 4.3 Critères de sortie V1.0.0 (D8.3)

1. POC J0 D2.3 validé sur la box du PO ✅
2. 25 tools implémentés et testés (unit + intégration synthétique + tests live SSH) ✅
3. 5 resources implémentées et testées ✅
4. Auth Bearer fonctionnel sur **Claude Code ET MCP Inspector** ✅ (ADR-0018 : Claude Desktop remplacé par Claude Code + MCP Inspector comme clients de validation V1 — Claude Desktop supporté via `mcp-remote`)
5. Sanitisation validée par le PO sur sa propre installation (sanity check à l'œil humain — D15.6) ✅
6. Matrice de couverture skill jeedom-audit D5.8 produite et lue par le PO ✅
7. README + identité produit Holmes MCP rédigés ✅
8. Plugin packagé installable depuis sources ✅
9. **Documentation utilisateur MkDocs complète** publiée sur GitHub Pages, référencée dans `info.json`, lue et validée par le PO avant soumission market ✅

### 4.4 Bêta privée avant release publique (D8.4)

Entre V1.0.0 sortable et V1.0.0 public sur le market :
- Plugin testé sur la **seule box du PO pendant au moins 2 semaines d'usage réel**
- Aucun crash daemon pendant cette période
- Aucune fuite de données identifiée
- Au moins **5 sessions Claude Desktop / Cursor réelles** menées par le PO (pas juste "ça démarre")

Puis soumission market directement en statut **bêta** (pas stable). Conversion bêta → stable après quelques semaines de retours communautaires positifs.

---

## 5. Jalons J0-J7

**Total estimé : ~15-20 sessions Claude Code + 2+ semaines bêta privée.**

---

### J0 — Bootstrap + POC faisabilité

**Objectif principal** : valider techniquement l'architecture (POC D2.3 — 7 hypothèses), bootstrapper la structure du repo, trancher les décisions 🔵 J0, vérifier les pré-requis externes.

**Durée indicative** : 2-3 sessions Claude Code

**Livrables Claude Code** :
- Structure complète du repo (`core/`, `desktop/`, `resources/holmesMcpd/`, `plugin_info/`, `tests/`, `.github/`)
- `.gitignore` strict + pre-commit hook (scan credentials) + pre-push hook
- `plugin_info/info.json` (manifeste — `holmesMcp`, `hasOwnDeamon: true`, `hasDependency: true`, `require: "4.5"`)
- `plugin_info/packages.json` (deps apt + pip3 versionnées selon D9.1)
- `pyproject.toml` (ruff, pytest, config Python)
- `.gitattributes` (convention market Jeedom)
- `plugin_info/install.php` (hooks `holmesMcp_install/update/remove` avec création/suppression user MySQL RO)
- `holmesMcp.class.php` (enveloppe PHP : `deamon_start()`, `deamon_stop()`, `deamon_info()`, `dependancy_info()`, `dependancy_install()`)
- `holmesMcpd.py` (daemon Python "hello world MCP" avec tool fictif `hello` — POC D2.3)
- POC committé (branche `develop` ou `poc/j0`)
- ADR-0018 rédigée (résultat POC D2.3 — hypothèses 1 à 7)
- ADRs 0001 à 0017 étoffées (statut `draft` → `proposed`, à valider par le PO par lots de 3-5)
- Décisions 🔵 J0 tranchées et documentées en ADRs (D1.2, D3.2, D4bis.1, D4bis.2, D9.1, D10.3, D10.8, D11.6, D12.6, D12.7, D2.4)
- Branche `develop` créée, CI GitHub Actions minimale configurée (`ci.yml` : lint ruff + tests unit + intégration Docker MySQL)
- `docs/ROADMAP.md` mis à jour si nouvelles candidates émergent

**Livrables PO (matières physiques)** :
- **Avant J0** : confirmation copyright holder `jeedom-skills` unique (vérification `git log --pretty='%ae' | sort -u` côté Claude Code, confirmation PO)
- **J0 hypothèse #7** : ajout du serveur MCP dans Claude Desktop sur sa machine (URL + Bearer token) + rapport succès/échec connexion + invocation tool `hello`. *Timing : pendant la session J0 POC, à distance.*
- **J0 validation** : go/no-go sur le POC (décision d'engagement de la suite du PLANNING)

**Dépendances** : aucune (jalon initial)

**Critères d'avancement (DoD)** :
- [ ] 7 hypothèses POC D2.3 validées (dont hypothèse #7 Claude Desktop confirmée par PO)
- [ ] Décisions 🔵 J0 toutes tranchées et documentées (ADRs)
- [ ] Structure repo bootstrappée, `develop` créé, CI verte (lint + tests sur repo vide)
- [ ] Plugin installable depuis sources sur box PO via SSH Claude Code
- [ ] ID `holmesMcp` confirmé libre sur market Jeedom
- [ ] Copyright holder `jeedom-skills` vérifié (condition bascule licence AGPL)
- [ ] Pré-release tag `v0.1.0` committé

**Risques jalon** :
- Claude Desktop refuse HTTP non-TLS en LAN → plan B HTTPS self-signed (+1-2 jours)
- `CREATE USER` privilege absent sur install PO → message clair, workaround documenté
- ID `holmesMcp` pris sur market → escalade PO avec alternatives

---

### J1 — Couche `_core` + matrice de couverture skill

**Objectif principal** : implémenter les 4 modules de la couche d'accès (`_core/`) avec tests unitaires >80%, livrer la matrice de couverture D5.8.

**Durée indicative** : 3-4 sessions Claude Code

**Livrables Claude Code** :
- `_core/auth.py` — validation Bearer token, lookup token → user Jeedom, 401 si invalide
- `_core/db.py` — driver MySQL RO (`jeedom_mcp_ro`), escape SQL réservés (dérivé `db_query.py`), gestion erreurs connexion
- `_core/api.py` — client API JSON-RPC localhost, blacklist méthodes modifiantes (dérivé `api_call.py`), retry 1x
- `_core/logs.py` — lecture fichiers de log Jeedom, résolution dynamique des chemins (dérivé `logs_query.py`)
- Tests unitaires `tests/unit/_core/` avec >80% couverture (PyMySQL mocké, fixtures synthétiques)
- Fixtures synthétiques initiales `tests/fixtures/synthetic/` (schéma DB Jeedom, logs types)
- `docs/skill-coverage-matrix.md` — matrice WF1-WF13 jeedom-audit ↔ tools MCP V1 (D5.8)
- ADR de la matrice (couverture complète ou gaps documentés)
- Décisions 🔵 J1 tranchées : D6.3 (plafond énumération resources), D14.4 (détails UI logs), D15.2 (enrichissement liste plugins)

**Livrables PO** :
- Validation matrice D5.8 (lire et confirmer que les WF sont correctement mappés)
- Go/no-go sur éventuels tools manquants identifiés par la matrice

**Dépendances** : J0 validé (POC + décisions 🔵 J0 tranchées)

**Critères d'avancement (DoD)** :

- [x] 4 modules `_core/` implémentés, tests >80% sur chacun — 74 tests unitaires (100%), 18 tests intégration live (J1-3)
- [x] `_core/db.py` testé sur box réelle via SSH (ADR-0012 pivot : SSH > Docker CI — ADR-0018) + 2 bugs corrigés (socket unix, LIKE params)
- [x] `_core/auth.py` testé (token valide / invalide / absent → 401) — unit + intégration live
- [x] `_core/api.py` blacklist méthodes modifiantes vérifiée par test — unit + intégration live
- [x] Matrice D5.8 livrée dans `docs/skill-coverage-matrix.md` et validée par le PO (go J1-3 accordé)
- [x] Pré-release tag `v0.2.0` ← posé en fin J1

---

### J2 — Couche `_domain` + sanitiseur

**Objectif principal** : implémenter les 4 modules de logique métier (`_domain/`) dérivés des scripts jeedom-audit, avec couverture de tests 100% sur `sanitize.py`.

**Durée indicative** : 2-3 sessions Claude Code

**Livrables Claude Code** :
- `_domain/usage_graph.py` — graphe d'usage scénarios/commandes (dérivé `usage_graph.py`)
- `_domain/scenario_walker.py` — walker arbre scénario (dérivé `scenario_tree_walker.py`)
- `_domain/cmd_refs.py` — résolveur `#[O][E][C]#` ↔ `#cmdId#` (dérivé `resolve_cmd_refs.py`)
- `_domain/sanitize.py` — 3 mécanismes cumulés : whitelist champs exposables + regex clés JSON + hard-code plugins ; mask + count (dérivé + enrichi `_common/sensitive_fields.py`)
- Tests unitaires `tests/unit/_domain/` — **couverture 100% `sanitize.py`** (fixtures avec credentials dans tous les emplacements connus)
- Liste plugins hard-codés enrichie (D15.2 : revue des 10 plugins Jeedom les plus installés)
- ADR-0017 `sanitize.py` mise à jour (statut `draft` → `proposed`)

**Livrables PO** :
- Validation de la liste des plugins hard-codés (regarder la liste, confirmer qu'elle couvre les plugins de son install)

**Dépendances** : J1 validé (couche `_core/` testée)

**Critères d'avancement (DoD)** :
- [ ] 4 modules `_domain/` implémentés, tests unitaires présents
- [ ] **100% couverture `sanitize.py`**
- [ ] Tests de sanitisation : aucun credential connu ne passe dans les fixtures de test
- [ ] Liste plugins hard-codés validée par le PO
- [ ] Pré-release tag `v0.3.0`

---

### J3-J4 — Tools familles 1, 2, 3 (18 tools)

**Objectif principal** : implémenter les 3 premières familles de tools (découverte d'install, équipements/commandes, scénarios) avec intégration `_core/` + `_domain/`, tests d'intégration sur fixtures synthétiques.

**Durée indicative** : 4-5 sessions Claude Code

**Livrables Claude Code** :

*Famille 1 — Découverte d'install (4 tools)* :
- `get_install_overview` — snapshot général (version Jeedom, nb équipements/scénarios/plugins, état général)
- `list_objects` — hiérarchie des objets Jeedom (pièces)
- `list_plugins` — plugins installés avec version et état
- `get_config` — config table `config` (namespace, key_pattern, sanitisation runtime)

*Famille 2 — Équipements et commandes (7 tools)* :
- `list_equipments` — liste filtrable (objet, plugin, état actif)
- `find_equipments_advanced` — filtres avancés
- `get_equipment` — détail complet (commandes, config sanitisée, état)
- `find_equipment_by_name` — recherche fuzzy
- `list_commands` — commandes d'un équipement
- `find_commands_advanced` — filtres avancés
- `get_command_history` — historique d'une commande info (live + archivé)

*Famille 3 — Scénarios (7 tools)* :
- `list_scenarios` — liste filtrable, état activation
- `find_scenarios_advanced` — filtres avancés
- `get_scenario` — détail complet (déclencheurs, structure, dernier lancement, log dernier run)
- `get_scenario_structure` — arbre brut (nœuds, parents, types, expressions) — machine-friendly
- `describe_scenario` — description fidèle au rendu UI Jeedom, résolution `#[O][E][C]#` systématique — LLM-friendly
- `find_scenario_dependencies` — graphe d'usage (`usage_graph.py`)
- `get_scenario_log` — log du dernier run d'un scénario

- Module `mcp_server.py` — bootstrap MCP, registration des 18 tools, routing vers les modules tools/
- Tests d'intégration `tests/integration/tools/` sur fixtures synthétiques (MySQL Docker)

**Livrables PO** :
- Validation fonctionnelle textuelle (lire 2-3 descriptions de tools en langage naturel et confirmer la pertinence)

**Dépendances** : J2 validé (couche `_domain/` + sanitiseur testés)

**Critères d'avancement (DoD)** :
- [x] 18 tools implémentés avec schémas in/out stables — F1+F2+F3 livrés (J3-1 à J3-3)
- [x] Tests d'intégration live sur box réelle — 93/93 (ADR-0018 accepted : SSH > Docker CI)
- [x] Sanitisation systématique vérifiée par test — 490 ut, 100% sanitize.py, bugs whitelist corrigés J3-5
- [x] `mcp_server.py` registration + invocation 18 tools — smoke tests MCP validés (`tools/list` = 18)
- [x] Pré-release tag `v0.4.0` (J3-4) + `v0.4.1` (J3-5 audit fixes)

---

### J5 — Tools familles 4, 5, 6 + `query_sql` + 5 resources

**Objectif principal** : compléter les 7 tools restants, implémenter `query_sql` restreint et les 5 resources minimales.

**Durée indicative** : 2-3 sessions Claude Code

**Livrables Claude Code** :

*Famille 4 — Variables / dataStore (2 tools)* :
- `list_datastore_variables`
- `get_datastore_variable`

*Famille 5 — Logs et diagnostic (3 tools)* :
- `tail_log` — tail d'un log Jeedom avec grep optionnel
- `list_log_files` — liste des logs disponibles
- `get_health_summary` — daemons en panne, dépendances KO, messages système, cron en retard

*Famille 6 — Recherche transverse (1 tool)* :
- `search_text` — recherche dans noms d'équipements, commandes, scénarios, expressions

*Power-user / Audit (1 tool)* :
- `query_sql` — SELECT-only + blacklist tables sensibles + LIMIT obligatoire + sanitisation runtime + mini SQL cookbook dans la description

*5 resources minimales (D6.2)* :
- `jeedom://install/overview` → `get_install_overview`
- `jeedom://install/health` → `get_health_summary`
- `jeedom://scenario/{id}` → `describe_scenario` + `get_scenario_log`
- `jeedom://equipment/{id}` → `get_equipment`
- `jeedom://logs/today` → `tail_log` filtré 24h

- Plafond énumération resources décidé et implémenté (D6.3)
- Tests d'intégration sur les 7 tools + `query_sql` (refus INSERT/DELETE/DROP + blacklist tables + sanitisation)
- Tests resources sur fixtures synthétiques

**Livrables PO** :
- Validation fonctionnelle `query_sql` : test de refus sur commandes interdites (Claude Code fournit un rapport de test)

**Dépendances** : J3-J4 validés (18 premiers tools opérationnels)

**Critères d'avancement (DoD)** :
- [ ] 25 tools implémentés et testés (18 de J3-J4 + 7 de J5)
- [ ] `query_sql` : refus de toute requête non-SELECT testé, blacklist tables vérifiée par test
- [ ] 5 resources implémentées et testées
- [ ] MCP Inspector peut invoquer tous les 25 tools + 5 resources
- [ ] Pré-release tag `v0.5.0`

---

### J6 — Vue UI logs + observabilité + durcissement sanitisation

**Objectif principal** : finaliser l'observabilité (vue dédiée logs dans la page config plugin), enrichir la liste plugins hard-codés du sanitiseur, faire valider la sanitisation par le PO sur sa box.

**Durée indicative** : 2-3 sessions Claude Code

**Livrables Claude Code** :
- `desktop/php/holmesMcp.php` — page config plugin avec : tableau tokens par user, port, niveau de log + vue dédiée logs (parsing JSON Lines, tableau filtrable par user/tool/niveau/fenêtre temporelle, refresh auto)
- `desktop/js/holmesMcp.js` — JS de la vue config (framework natif Jeedom, pas de dépendance exotique)
- Rapport de sortie sanitisée (Claude Code exécute Holmes MCP sur la box réelle via SSH + lance les tools les plus exposants + fournit au PO le rapport sanitisé pour sanity check)
- Enrichissement `_domain/sanitize.py` avec liste plugins hard-codés complète (D15.2 enrichissement)
- ADR-0017 mise à jour (liste plugins V1.0.0)
- Tests live via SSH exécutés et résultats résumés dans `docs/sessions/`

**Livrables PO** :
- **SANITY CHECK SANITISATION** (non négociable — D15.6) : lire le rapport de sortie sanitisée fourni par Claude Code sur sa propre install + confirmer qu'aucun credential connu ne transparaît. *Timing : fourni à J6, délai de réponse attendu : même session ou session suivante.*

**Dépendances** : J5 validé (25 tools + 5 resources opérationnels)

**Critères d'avancement (DoD)** :
- [ ] Vue dédiée logs opérationnelle dans la page config plugin Jeedom (vérifiée par Claude Code via SSH)
- [ ] Rapport sanitisé fourni au PO et **sanity check PO réalisé** ✅
- [ ] Liste plugins hard-codés finalisée et documentée en ADR-0017
- [ ] Tests live exécutés + résumés en session
- [ ] Pré-release tag `v0.6.0`

---

### J7 — Doc utilisateur + bêta privée + release market

**Objectif principal** : livrer la documentation utilisateur MkDocs, finaliser l'identité produit, conduire la bêta privée sur la box du PO, soumettre au market en statut bêta.

**Durée indicative** : sessions Claude Code + 2+ semaines bêta privée PO + délai compte développeur Jeedom (plusieurs semaines)

---

#### J7-1 ✅ Documentation utilisateur MkDocs (2026-05-05)

- `docs/user/` : 12 sections MkDocs complètes
- `plugin_info/holmesMcp_icon.png` : icône market hibou Holmes (200×200 initiale)
- `mkdocs build --strict` OK

#### J7-2 ✅ Packaging market (2026-05-05)

- `plugin_info/info.json` : version 1.0.0, catégorie `programming`
- `plugin_info/changelog.md` : historique complet v0.0.0→v1.0.0 (langage utilisateur)
- `plugin_info/holmesMcp_icon.png` : format Jeedom conforme (309×348, zone 309×309 coins arrondis, 39px transparent bas)
- `README.md` : market-ready v1.0.0
- `docs/market/forum-developers-lounge.md` : post Developers' Lounge prêt à publier
- Commit `0eb3122`

#### J7-3 ✅ Polish UI page configuration (2026-05-05)

- `desktop/php/holmesMcp.php` : tokens masqués (8 chars + `••••••••••••••••`), bouton `fa-eye`, icônes `fa-cog` / `fa-key` / `fa-list-alt`
- `desktop/js/holmesMcp.js` : `toggleToken()` + `generateToken()` masque le nouveau token
- Commit `1da6f67` — rendu validé PO (capture)

**DoD** :

- [x] Tokens masqués par défaut avec bouton révéler
- [x] Sections avec icônes Font Awesome cohérentes avec le thème Jeedom
- [x] Rendu validé sur box PO (capture PO)

---

### J7bis — Améliorations Holmes MCP pré-migration jeedom-audit

**Objectif** : traiter les 4 items identifiés dans l'audit de migration jeedom-audit → Holmes MCP (session J8-audit, 2026-05-05) avant de démarrer la migration effective sur jeedom-skills. Aucun item n'est bloquant pour la migration, mais les traiter en amont garantit une meilleure qualité de vie pour tous les clients MCP.

**Démarrage** : à la clôture de J7 (J7-3 ✅) et après l'audit J8-audit ✅.

#### J7bis-1 — Nouvel outil + qualité query_sql + doc ✅

**Livraisons :**

- **Item A** — Nouvel outil `find_command_usages(cmd_id)` (Family 2 — équipements/commandes) : retourne triggers, conditions/actions, refs dataStore pour une commande donnée. SQL déjà documenté dans `sql-cookbook.md`. À ajouter dans `tools/equipments.py` + `mcp_server.py` + tests + doc.
- **Item B** — `query_sql()` : documenter le comportement LIMIT auto-injecté (50 si absent, max 200) dans la docstring de l'outil + section diagnostic de la doc MkDocs.
- **Item C** — `query_sql()` : auto-backtick des mots réservés MySQL connus dans le contexte Jeedom (`trigger`, `repeat`, `update`) dans le parser `tools/query_sql.py`.
- **Item D** — FAQ MkDocs : ajouter entrée "Jeedom 4.4.x est-il supporté ?" → Non, Holmes MCP cible Jeedom 4.5+ (Bookworm x86_64).

**DoD J7bis-1** :

- [x] `find_command_usages(cmd_id)` implémenté, testé (unit + intégration live), documenté
- [x] `query_sql()` docstring mise à jour (comportement LIMIT)
- [x] Parser `query_sql.py` : auto-backtick `trigger` / `repeat` / `update`
- [x] `docs/user/faq.md` : entrée Jeedom 4.4.x ajoutée
- [x] Tests unitaires 100% verts, ruff propre
- [x] `plugin_info/changelog.md` — entrée J7bis ajoutée
- [x] `plugin_info/info.json` — version incrémentée (`1.1.0`)
- [x] `docs/market/forum-developers-lounge.md` — relu, mis à jour si besoin

#### J7bis-2 — Audit live Holmes MCP + jeedom-audit

**Objectif** : valider Holmes MCP v1.1.0 en conditions réelles sur la box et auditer la couverture des 13 workflows jeedom-audit avec Holmes MCP comme source de données exclusive. Même nature que J8-audit, mais avec le nouvel outil `find_command_usages` disponible et les corrections J7bis-1 intégrées.

**Pré-requis** :

- Snapshot Proxmox avant la session (SSH + tests live)
- Daemon Holmes MCP démarré sur la box (`v1.1.0` déployé)
- SSH alias `Jeedom` opérationnel

**Livrables :**

- **Audit A — Tests d'intégration live complets** : lancer la suite `pytest tests/integration/` sur la box via SSH. Valider les 4 tests `TestFindCommandUsagesLive` (nouveau). Documenter tous les échecs/écarts.
- **Audit B — WF jeedom-audit × Holmes MCP** : pour chacun des 13 workflows de `docs/skill-coverage-matrix.md`, vérifier que Holmes MCP (v1.1.0) couvre le besoin end-to-end depuis Claude Code. Identifier les gaps résiduels.
- **Audit C — Qualité des réponses MCP** : sanity check sur 5-10 requêtes réelles depuis Claude Code sur la box du PO. Vérifier : sanitisation, pertinence, absence de crash.
- **Audit D — Rapport d'audit** : document `docs/state/audit-J7bis-2.md` listant : items ✅ / ⚠️ / 🔴, bugs identifiés, gaps résiduels, recommandations pour J8.

**DoD J7bis-2** :

- [ ] Suite intégration live exécutée — résultats documentés
- [ ] `find_command_usages` validé live sur la box
- [ ] 13 WF jeedom-audit revus — matrice mise à jour si besoin
- [ ] Rapport `docs/state/audit-J7bis-2.md` rédigé
- [ ] Zéro crash daemon pendant la session
- [ ] Items bloquants pour J8 identifiés (ou confirmation : aucun)

---

### J8 — Bêta privée

**Objectif** : valider le plugin en conditions réelles sur la box du PO avant toute publication market. La bêta combine deux axes : (1) sessions Claude Code directes sur Holmes MCP, (2) migration de jeedom-audit (branche `develop` sur `jeedom-skills`) pour utiliser Holmes MCP comme source de données exclusive — validation bout-en-bout conforme à ADR-0019/0020.

**Démarrage** : à la clôture de J7bis.

**Client retenu** : Claude Code (HTTP LAN natif, déjà validé J0-3) + MCP Inspector pour le debug. *(Tranché J8-1 — 2026-05-05.)*

#### Critères de sortie bêta (DoD J8)

**Activité PO** :

- [ ] 5 sessions de test réelles minimum avec Claude Code + Holmes MCP
- [ ] Zéro crash daemon sur la durée de la bêta
- [ ] Zéro fuite de données observée (sanity check régulier)
- [ ] 2+ semaines de bêta effective
- [ ] PO déclare la bêta fermée

**Migration jeedom-audit (branche develop jeedom-skills)** :

- [ ] Branche `develop` créée sur `jeedom-skills`
- [ ] jeedom-audit migré : SSH/MySQL directs remplacés par appels Holmes MCP
- [ ] 12/13 workflows opérationnels sur la branche develop
- [ ] WF6 fonctionnel via `find_command_usages()` (livré en J7bis) + `query_sql()`

**Packaging market (DoD J8 — règle jalons futurs)** :

- [ ] `plugin_info/changelog.md` — entrée J8 ajoutée
- [ ] `plugin_info/info.json` — version incrémentée si livraisons code en J8
- [ ] `docs/market/forum-developers-lounge.md` relu et mis à jour si besoin

---

## 6. Jalon Jx — Publication market (numéro attribué par le PO quand il le décide)

Jalon flottant, déclenché par le PO quand les deux conditions sont réunies :

1. **Compte développeur Jeedom reçu** (demandé 2026-05-05, délai annoncé plusieurs semaines)
2. **Bêta privée fermée** (2+ semaines, 5 sessions réelles, zéro crash, zéro fuite)

Le numéro (J8, J9…) sera attribué par le PO au moment où il décide de déclencher le jalon, selon les jalons effectivement réalisés entre-temps.

### Contenu de Jx

**Pré-requis Claude Code (vérifier avant de déclencher)** :

- `plugin_info/info.json` version à jour avec le dernier jalon
- `plugin_info/changelog.md` entrée ajoutée pour chaque jalon depuis J7-2
- `docs/market/forum-developers-lounge.md` relu et mis à jour si périmètre a évolué
- Annonce forum grand public rédigée (texte à produire en début de Jx)

**Séquence** :

1. Claude Code vérifie et met à jour le packaging (changelog, info.json, post forum)
2. PO publie le post Developers' Lounge sur community.jeedom.com
3. PO soumet le plugin sur le portail market Jeedom en canal **bêta** (branche `main` du dernier tag stable)
4. Claude Code tag + PROJECT_STATE.md mis à jour
5. Claude Code rédige l'annonce forum grand public → PO publie

**Livrables PO (bloquants)** :

- Confirmation compte développeur reçu
- 3-5 captures d'écran UI Jeedom à jour (page config, état daemon, vue activité MCP)
- Validation Claude Desktop finale sur sa machine (D8.3 critère #4)
- Attestation bêta privée : 2+ semaines, 5 sessions réelles, zéro incident bloquant

**DoD Jx** :

- [ ] Packaging market à jour (changelog, info.json, icône)
- [ ] Post Developers' Lounge publié par le PO
- [ ] Plugin soumis sur le market Jeedom en statut bêta
- [ ] Annonce forum grand public publiée par le PO

---

### Règle DoD pour les jalons J8, J9… (et tout jalon futur)

**Chaque jalon futur doit inclure dans son DoD la mise à jour du packaging market** :

- [ ] `plugin_info/changelog.md` — entrée ajoutée pour ce jalon (langage utilisateur)
- [ ] `plugin_info/info.json` — version incrémentée (`1.x.0`)
- [ ] `docs/market/forum-developers-lounge.md` — relu, mis à jour si fonctionnalités nouvelles

Cela garantit que le packaging est toujours prêt à déclencher Jx sans retard, quel que soit le moment choisi par le PO.

---

## 7. Pré-requis externes (checklist J0)

Ces éléments doivent être traités en J0, indépendamment du code Holmes MCP.

| Pré-requis | Responsable | Action | Statut |
|---|---|---|---|
| Vérification copyright holder `jeedom-skills` | Claude Code (lecture `git log`) + confirmation PO | `git log --pretty='%ae' | sort -u` côté jeedom-skills | 🔴 À faire J0 |
| ADR de relicence `jeedom-skills` MIT→AGPL | Claude Code (sur repo jeedom-skills) | Rédiger + soumettre PO | 🔴 À faire J0 (si copyright OK) |
| Commit relicence + CHANGELOG + communication forum | PO | Commit `LICENSE` + entrée CHANGELOG + annonce forum conjointe V1.0.0 | 🔴 Co-événement J7 |

Si la vérification du copyright révèle une contribution externe → escalade PO avec options (consentement / réécriture / fallback MIT).

---

## 8. Roadmap V1.x / V2+

Voir `docs/ROADMAP.md`. Les candidates identifiées depuis le brief sont listées et statutées `draft` dans ce fichier. Tout nouveau besoin émergent pendant V1 → ROADMAP.md (anti-drift D8.2), pas en V1.

---

## 9. ADRs initiales

17 ADRs esquissées en `docs/decisions/ADR-0001.md` à `ADR-0017.md` (statut `draft` à l'issue de cette session de planning, à étoffer en J0 vers `proposed` par lots de 3-5 pour validation PO).

Deux ADRs futures réservées :
- `ADR-0018` : résultat du POC D2.3 (à rédiger post-POC J0)
- `ADR-0019` : couverture fonctionnelle skill jeedom-audit D5.8 (à rédiger post-J1)

Autres ADRs à créer en J0/J1 pour les décisions 🔵 (port défaut, driver MySQL, libs Python, lint, MkDocs, doc embarquée, plugins hard-codés sanitiseur, etc.) — numérotation au fil de l'eau à partir de ADR-0020.

---

## 10. Annexe — Glossaire

| Terme | Définition |
|---|---|
| **MCP** | Model Context Protocol (Anthropic) — protocole JSON-RPC 2.0 permettant à un client LLM d'invoquer outils et données d'un serveur tiers |
| **Tool MCP** | Fonction appelable (verbe paramétré) — le LLM décide de l'appeler |
| **Resource MCP** | URI attachable par l'utilisateur dans son client (donnée navigable) |
| **Streamable HTTP** | Transport HTTP de la spec MCP 2025-03-26+ (remplace HTTP+SSE déprécié) |
| **Plugin Jeedom** | Assemblage `info.json` + classe PHP + vues + optionnellement daemon, distribuable via le Market Jeedom |
| **Daemon (Jeedom)** | Processus permanent lancé/arrêté par hooks `deamon_*` (graphie officielle avec faute, conservée par le core) |
| **eqLogic** | Équipement Jeedom (table `eqLogic`), porte un `eqType_name` désignant le plugin owner |
| **cmd** | Commande Jeedom (table `cmd`). Type info (lecture) ou action (écriture) |
| **scenarioElement / scenarioSubElement / scenarioExpression** | Hiérarchie des nœuds d'un scénario Jeedom |
| **dataStore** | Variables persistantes Jeedom (table `dataStore`) |
| **history / historyArch** | Tables d'historisation des commandes info |
| **`#[O][E][C]#`** | Convention de nommage `#[Objet][Équipement][Commande]#`, forme humaine de `#cmdId#` |
| **logicalId** | Identifiant logique plugin-spécifique (jMQTT porte le topic MQTT, etc.) |
| **Type Générique** | Classification orthogonale des commandes (Lumière, Volet, Thermostat…) |
| **packages.json** | Fichier de déclaration moderne des dépendances plugin Jeedom (4.2+) — sections apt, pip3 |
| **MCP Inspector** | Outil officiel Anthropic pour tester un serveur MCP (tools/list, invocations) |
| **Sphère jeedom-audit** | Ensemble cohérent jeedom-audit (skill Claude Code) + Holmes MCP (plugin Jeedom), couplés à terme |
| **ADR** | Architecture Decision Record — fichier markdown dans `docs/decisions/` documentant une décision structurante |
| **Bêta privée** | Phase de test sur la seule box du PO avant soumission market (D8.4) |
| **Bêta market** | Statut de release sur le market Jeedom avant conversion stable (D12.2) |
| **Clean room** | Posture de conception : sources autorisées uniquement = brief + ADRs sources + scripts jeedom-audit + spec MCP Anthropic + doc Jeedom officielle |
