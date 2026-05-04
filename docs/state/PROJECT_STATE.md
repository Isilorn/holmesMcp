# PROJECT_STATE.md — État courant du projet Holmes MCP

> Mis à jour à chaque fin de session significative. Source de vérité pour la continuité entre sessions Claude Code.

---

## État général

| Champ | Valeur |
|---|---|
| **Version courante** | `v0.4.0` (J3-J4 ✅, J3-4bis ✅ runtime API, J3-5 ✅ audit+fixes) |
| **Jalon en cours** | J5 — 7 tools + query_sql + 5 resources |
| **Branche de travail** | `develop` |
| **Dernière session** | `2026-05-04-j5-2` |
| **Prochaine session** | `J5-3` — tests d'intégration live (8 tools F4/F5/F6 + query_sql) + corrections schéma + smoke test 25 tools |
| **Statut global** | 🟠 EN COURS — J0 ✅, J1 ✅ (v0.2.0), J2 ✅ (v0.3.0), J3-J4 ✅ (v0.4.0, 18 tools), J3-4bis ✅ (runtime API), J3-5 ✅ (audit 18 tools, 490 ut, 93 intég), J5-1 ✅ (24 tools, 557 ut), J5-2 ✅ (25 tools, 626 ut) |

---

## Jalon J0 ✅ Clôturé (2026-05-03)

### J0-1 ✅ Bootstrap repo + outils dev (2026-05-03)

- Structure complète du plugin (PHP shell, daemon Python POC-ready, tests, CI)
- Gardes-fous : `.gitignore` strict + hooks pre-commit/pre-push (scan credentials)
- D9.1 ✅ : httpx + sqlparse + structlog + pymysql → ADR-0002 proposed
- D11.6 ✅ : ruff → ADR-0002 proposed
- D10.3 ✅ : docs/ embarqué dans main → ADR-0014 proposed
- D12.6 ✅ : MkDocs Material + docs.yml CI → ADR-0014 proposed
- Scripts dev testés et validés : `dev/add-sudo-temp.sh` + `dev/remove-sudo-temp.sh` + `dev/secrets.cfg`

### J0-2 ✅ SSH + POC daemon (2026-05-03)

- D3.2 ✅ : port défaut **8765** (libre sur la box, aucune collision plugins)
- D4bis.1 ✅ : PyMySQL confirmé (MariaDB 10.x Bookworm, localhost)
- D4bis.2 ✅ : `CREATE USER` via `sudo mysql` (unix_socket root, user jeedom trop restrictif)
- D2.4 ✅ : venv natif Jeedom (`resources/python_venv/`) — `system::update()` Jeedom 4.4.9+
- Plugin installé sur la box, dépendances OK, daemon UP (PID confirmé, state:ok)
- `tools/list` → tool `hello` retourné via Streamable HTTP — hypothèses D2.3 #1-#6 validées
- Bugs corrigés en session : `realpath()` symlink venv, `FastMCP.run()` API 1.27.0, `list_tools()` async
- Infrastructure MySQL : user `jeedom_mcp_ro` créé, `GRANT SELECT ON jeedom.*`, mdp dans `/etc/holmes_mcp_ro.conf`

### J0-3 ✅ Validation client MCP LAN (2026-05-03)

- Hypothèse #7 ✅ validée via **Claude Code** (HTTP LAN natif, `type: "http"` dans `.mcp.json`)
- Claude Desktop : ne supporte pas HTTP LAN direct — contournement via `mcp-remote` (stdio→HTTP)
- Plan B HTTPS self-signed **abandonné** — HTTP suffisant pour V1
- ADR-0018 rédigée et accepted

### J0 ✅ Clôturé (2026-05-03)

Toutes les hypothèses D2.3 validées. Plan B HTTPS self-signed abandonné (HTTP suffisant). ADR-0018 accepted. J0-3bis annulée.

**Stratégie de test validée (ADR-0018) :** les tests d'intégration V1 sont réalisés en priorité depuis **Claude Code**. C'est Claude Code qui les exécute via SSH sur la box PO — sans intervention du PO pour les tests techniques. Le PO intervient uniquement pour les validations de matière (sanity check UI, critère D8.3 #5).

### J1-1 ✅ Couche `_core` + tests unitaires (2026-05-03)

- `_core/db.py` : PyMySQL read-only, config `/etc/holmes_mcp_ro.conf`, escape mots réservés MySQL
- `_core/auth.py` : `TokenStore` (résolution token→login via tables `config`+`user`), `BearerAuthMiddleware` ASGI pur
- `_core/api.py` : JSON-RPC localhost, blacklist 12 verbes écriture V1, retry transport
- `_core/logs.py` : lecture fichiers directe, validation nom anti-traversée, tail+grep
- `holmesMcpd.py` : structlog JSON Lines (D9.1), `--jeedom-apikey`, uvicorn direct + middleware auth injecté
- `holmesMcp.class.php` : passage `--jeedom-apikey jeedom::getApiKey()` au démarrage daemon
- `pyproject.toml` : dépendances test ajoutées (`pymysql`, `structlog`, `pytest-asyncio`, `pytest-cov`)
- 72 tests unitaires — 72/72 passés
- D1.2 ✅ spec MCP 2025-03-26 | D14.4 ✅ HTML natif Jeedom + AJAX | D15.2 ✅ 10 plugins hard-codés

### J1-2 ✅ Matrice couverture D5.8 (2026-05-03)

- `docs/skill-coverage-matrix.md` : 13/13 WF jeedom-audit couverts — 0 tool manquant
- ADR-0019 accepted : bascule jeedom-audit → consommatrice Holmes MCP validée sans ajout V1
- Simplifications vs jeedom-audit : `router.py` non porté (daemon sur la box), `resolve_cmd_refs.py` intégré dans `describe_scenario`
- D5.8 ✅ tranché

### J1-3 ✅ Tests d'intégration + D6.3 (2026-05-04)

- Fixtures synthétiques : `tests/fixtures/synthetic/` (config_tokens, eqlogics, log_sample)
- Tests d'intégration `tests/integration/` : 18/19 passés (1 skip attendu — clé API chiffrée crypt:)
  - `_core/db.py` ✅ : connexion socket unix, SELECT 1, tables présentes, comptages D6.3
  - `_core/auth.py` ✅ : TokenStore chargé depuis DB live (1 token trouvé)
  - `_core/api.py` ✅ : blacklist save/exec validée, version OK, eqLogic::all skip (crypt:)
  - `_core/logs.py` ✅ : holmesMcp log résolu, tail, grep, validations traversal
- **D6.3 mesuré sur box PO** : 217 eqLogics, 6212 cmds, 62 scenarios, 36 objects
- **2 bugs _core/ corrigés** :
  - `db.py` : connexion TCP `127.0.0.1` → socket unix `/run/mysqld/mysqld.sock` (GRANT @localhost)
  - `db.py` : `query()` passait `params=()` vide → PyMySQL formatait `%_` dans LIKE → fix `None`
- Déploiement daemon avec `--jeedom-apikey` (manquant en prod) — UP et authentifié ✅
- 74 tests unitaires (100% passés), ruff propre
- ADR-0012 accepted, ci.yml corrigé (job Docker supprimé, cohérent ADR-0012+ADR-0018)

### J1 ✅ Clôturé (2026-05-04) — tag `v0.2.0`

DoD intégralement coché (voir `docs/PLANNING.md` §J1). Branche `develop` créée pour J2.

---

## Jalon J2 — _domain + sanitiseur (en cours)

**Objectif** : implémenter les 4 modules `_domain/` dérivés des scripts jeedom-audit, avec couverture 100% sur `sanitize.py`.

### J2-1 ✅ `sanitize.py` — 3 mécanismes + couverture 100% (2026-05-04)

- `_domain/sanitize.py` : 3 mécanismes cumulatifs (D15.1-D15.2)
  - Mech 1 : whitelist par table (13 tables : eqLogic, cmd, scenario, object, dataStore,
    config, plugin, history, historyArch, scenarioElement, scenarioSubElement,
    scenarioExpression, interactDef)
  - Mech 2 : regex `_BLOB_KEY_RE` sur clés JSON des blobs (configuration, options)
  - Mech 3 : extras par plugin — 15 plugins (10 initiaux D15.2 + 5 install PO :
    Alarme, Jeedom Connect, MQTT Manager, Script, Virtuel)
- Comportement mask+count : `FILTERED = "***FILTERED***"` + `_filtered_fields`
- Cas spécial config table : key visible, value masquée si key sensible (transparence LLM)
- Parsing récursif des blobs JSON imbriqués
- `tests/unit/_domain/test_sanitize.py` : 158 tests, **100% couverture** sanitize.py (D15.5)
  - 10 fixtures "no credential in output" couvrant tous les emplacements connus
- Ruff propre — commit `7ce211e`

**Liste plugins hard-codés validée par le PO (D15.2 enrichi J2-1)** : 15 plugins.
Plugins install PO confirmés : jMQTT ✅, Agenda ✅, Alarme (ajouté), Thermostat ✅,
Jeedom Connect (ajouté), Script (ajouté), MQTT Manager (ajouté), Virtuel (ajouté).

### J2-2 ✅ `usage_graph.py` + `scenario_walker.py` — 100% coverage (2026-05-04)

- `_domain/usage_graph.py` : graphe d'usage pour cmd, eqLogic, scénario
  - `resolve(target_type, target_id, conn)` — dispatch cmd / eqLogic / scenario
  - Déduplication triggers/conditions/actions inter-commandes (cible eqLogic)
  - `false_positive_warnings` pour les blocs code PHP
- `_domain/scenario_walker.py` : parcours récursif d'un scénario Jeedom
  - `walk(scenario_id, conn, max_depth, follow_scenario_calls)` — API publique
  - Anti-cycle inter-scénarios (`_visited_scenarios`), troncature à 100 sous-éléments
  - Suivi des appels `scenario/start` avec profondeur configurable
- `tests/unit/_domain/test_usage_graph.py` : 30 tests, **100% couverture**
- `tests/unit/_domain/test_scenario_walker.py` : 49 tests, **100% couverture**
- **311 tests unitaires — 311/311 passés**. Ruff propre.

### J2-3 ✅ `cmd_refs.py` + intégration `_domain/` + ADR-0017 proposed (2026-05-04)

- `_domain/cmd_refs.py` : résolveur `#cmdId#` → `#[O][E][C]#` batch SQL
  - `resolve(text, conn)` — extraction IDs, requête batch, substitution + `#ID_NON_RÉSOLU:X#`
  - `_fetch_names(ids, conn)` — jointure `cmd/eqLogic/object`, COALESCE objet NULL
  - API : `db.query(conn, sql, params)` avec placeholders `%s` (PyMySQL)
- `tests/unit/_domain/test_cmd_refs.py` : 20 tests, **100% couverture** cmd_refs.py
- `docs/decisions/ADR-0017.md` : statut `draft` → `proposed` (implémentation complète documentée)
- `mcp_server.py` : commentaire d'architecture `_domain/` prêt pour J3
- **331 tests unitaires — 331/331 passés**. Couverture globale 85,87%. Ruff propre.

### J2 ✅ Clôturé (2026-05-04) — tag `v0.3.0`

DoD intégralement coché (voir `docs/PLANNING.md` §J2). 4/4 modules `_domain/` livrés avec couverture 100% sur `sanitize.py` et `cmd_refs.py`.

---

## Jalon J3-J4 — Tools familles 1, 2, 3 (18 tools)

**Objectif** : implémenter les 18 tools en 3 familles avec intégration `_core/` + `_domain/`, tests unitaires, puis tests d'intégration sur box réelle (J3-4).

**Plan de sous-sessions** :

- J3-1 ✅ : Famille 1 (4 tools découverte)
- J3-2 ✅ : Famille 2 (7 tools équipements/commandes)
- J3-3 ✅ : Famille 3 (7 tools scénarios)
- J3-4 ✅ : tests intégration live + corrections schema + déploiement + smoke tests
- J3-4bis ✅ : enrichissement runtime API JSON-RPC (state/lastLaunch + currentValue/collectDate)
- J3-5 🔜 : audit exhaustif 18 tools (brief + documentation + besoins jeedom-audit)

### J3-1 ✅ Famille 1 — 4 tools découverte d'install (2026-05-04)

- `tools/discovery.py` : 4 tools MySQL RO
  - `get_install_overview` : version Jeedom + comptages (eq/scen/plugins/objets/cmds)
  - `list_objects` : hiérarchie objets/pièces, paginé (LIMIT 500), sanitisé
  - `list_plugins` : plugins installés (id/name/version/state/logical_id), sanitisé
  - `get_config` : config par namespace plugin + filtre LIKE optionnel, sanitisé — valeurs sensibles masquées, clé visible (transparence LLM)
- `mcp_server.py` : registration famille 1, tool POC `hello` retiré
- `tests/unit/tools/test_discovery.py` : 27 tests — 358/358 passés, ruff propre
- Commit `413f3e0`

### J3-2 ✅ Famille 2 — 7 tools équipements/commandes (2026-05-04)

- `tools/equipments.py` : 7 tools MySQL RO (tables eqLogic, cmd, history, historyArch)
  - `list_equipments` : liste filtrable (object_id, plugin/eqType_name, is_enable), paginée (LIMIT 100)
  - `find_equipments_advanced` : filtres combinables (name LIKE, object_id, plugin, is_enable, generic_type, tags LIKE), LIMIT 50
  - `get_equipment` : détail complet eqLogic + ses commandes, config sanitisée (blobs configuration/status inclus)
  - `find_equipment_by_name` : recherche LIKE %name%, LIMIT 50
  - `list_commands` : commandes d'un équipement, filtre optionnel type (info/action), paginée (LIMIT 200)
  - `find_commands_advanced` : filtres combinables (name, equipment_id, type, subType, generic_type, isHistorized), LIMIT 50
  - `get_command_history` : historique récent (table `history`) + archivé (`historyArch`), LIMIT 100 par table
- `mcp_server.py` : `_register_family2` ajouté — 11 tools enregistrés (4 F1 + 7 F2)
- `tests/unit/tools/test_equipments.py` : 43 tests — **401/401 passés**. Ruff propre.

### J3-3 ✅ Famille 3 — 7 tools scénarios (2026-05-04)

- `tools/scenarios.py` : 7 tools (MySQL RO + `_domain/` + `_core/logs`)
  - `list_scenarios(group, is_active, limit=100, offset)` : liste paginée filtrable, sanitisée
  - `find_scenarios_advanced(name_contains, group, is_active, trigger_type, limit=50)` : filtres combinables
  - `get_scenario(scenario_id)` : détail complet (trigger, group, isActive, mode, timeout…), sanitisé
  - `get_scenario_structure(scenario_id, max_depth=3, follow_scenario_calls=0)` : arbre brut via `scenario_walker`, machine-friendly
  - `describe_scenario(scenario_id)` : LLM-friendly, résolution `#cmdId#` → `#[O][E][C]#` systématique via `cmd_refs` + `_humanize` closures
  - `find_scenario_dependencies(scenario_id)` : graphe callers via `usage_graph.resolve('scenario', …)`
  - `get_scenario_log(scenario_id, lines=100)` : `scenarioLog/scenario{id}.log`, max 500 lignes
- `mcp_server.py` : `_register_family3` ajouté — **18 tools enregistrés** (4 F1 + 7 F2 + 7 F3)
- `tests/unit/tools/test_scenarios.py` : 44 tests — **447/447 passés**. Ruff propre. Commit `3385dca`

### J3-4 ✅ Tests intégration live + corrections schema (2026-05-04)

- `tests/integration/tools/` : 68 tests live (sur box réelle, `sudo -u www-data`)
  - `test_discovery_live.py` : 16 tests F1 (discovery)
  - `test_equipments_live.py` : 28 tests F2 (equipments)
  - `test_scenarios_live.py` : 24 tests F3 (scenarios)
- **4 bugs schema corrigés** (découverts sur box réelle Jeedom 4.5.3) :
  - `discovery.py` : table `plugin` inexistante → `update WHERE type='plugin'` ; colonne `order` absente dans `object` → `position`
  - `equipments.py` : colonne `id` absente dans `history`/`historyArch` → supprimée du SELECT
  - `scenarios.py` : colonnes `lastLaunch` et `state` absentes dans `scenario` → supprimées de `_SCEN_COLS`
  - `usage_graph.py` : `%` littéraux non échappés dans CONCAT → `%%` (PyMySQL formatage)
- **Smoke tests MCP** validés en HTTP sur la box :
  - `tools/list` → 18 tools retournés ✅
  - `get_install_overview` → `jeedom_version: 4.5.3`, 217 eq, 62 scénarios, 6212 cmds ✅
  - `list_scenarios(limit=3)` → 3 scénarios retournés ✅
- **68/68 tests intégration live** passés. **447/447 tests unitaires** passés. Ruff propre.
- Tag `v0.4.0` — J3-J4 ✅ clôturé.

### J3-4bis ✅ Enrichissement runtime API JSON-RPC (2026-05-04)

**Contexte** : audit post-J3-4 révèle que `lastLaunch`/`state` (scénarios) et `currentValue`/`collectDate` (commandes info) sont absents des retours tools. Ces champs sont PHP runtime-only — absents de la table MySQL `scenario`. D4bis.6 les planifiait via API JSON-RPC, mais `_core/api.py` (déjà implémenté) n'était jamais appelé par les tools.

**Enrichissement scénarios (`tools/scenarios.py`)** :

- `_fetch_runtime_map(apikey)` : un appel `scenario::all` → `{id: {state, lastLaunch}}`. Retourne `{}` si apikey vide ou API KO.
- `_fetch_runtime_single(apikey, scenario_id)` : un appel `scenario::byId` pour un scénario unique.
- `_merge_runtime(scenarios_list, runtime_map)` : injection in-place `state` + `lastLaunch`.
- 4 tools enrichis : `list_scenarios`, `find_scenarios_advanced`, `get_scenario`, `describe_scenario` — signature `apikey: str = ''` (dégradation gracieuse si absent).

**Enrichissement équipements (`tools/equipments.py`)** :

- `_fetch_cmd_runtime_map(apikey, equipment_id)` : un appel `eqLogic::fullById` → `{cmd_id: {currentValue, collectDate}}`.
- `_inject_cmd_runtime(cmds, runtime_map)` : injection sur commandes `type == 'info'` uniquement.
- 2 tools enrichis : `get_equipment`, `list_commands` — signature `apikey: str = ''`.
- `list_equipments`, `find_equipments_advanced`, `find_commands_advanced` : non enrichis (appels liste, coût prohibitif N×API).

**`mcp_server.py`** : `build_mcp` passe `apikey = args.jeedom_apikey` à `_register_family2` et `_register_family3` ; closures capturent `apikey`.

**Fixture `jeedom_apikey` réécrite (`tests/integration/conftest.py`)** :

- Lit la clé déchiffrée depuis `/proc/<pid>/cmdline` du daemon holmesMcp (PID dans `/tmp/jeedom/holmesMcp/daemon.pid`).
- Raison : la table `config` stocke la clé chiffrée `crypt:...` (inutilisable pour les appels API directs).

**Nouveaux tests** :

- Unitaires : 29 nouveaux (3 classes `test_scenarios.py` : `TestListScenariosRuntime`, `TestGetScenarioRuntime`, `TestFetchRuntimeHelpers` ; 2 classes `test_equipments.py` : `TestGetEquipmentRuntime`, `TestFetchCmdRuntimeMap`)
- Intégration live : 8 nouveaux (`test_state_and_last_launch_present` × 4 dans scenarios, `test_info_cmds_have_current_value` × 2 dans equipments)

**93/93 tests intégration live** passés. **476/476 tests unitaires** passés. Ruff propre. Commit `82ae6ef` sur `develop`.

---

## Jalon J5 — Tools familles 4, 5, 6 + `query_sql` + 5 resources

**Objectif** : compléter les 7 tools restants + `query_sql` + 5 resources → 25 tools + 5 resources, tag `v0.5.0`.

**Plan de sous-sessions** :

- J5-1 ✅ : Familles 4+5+6 (7 tools) + tests unitaires
- J5-2 ✅ : `query_sql` + tests unitaires
- J5-3 🔜 : Tests d'intégration live (8 tools) + corrections schéma ← **prochaine**
- J5-4 🔜 : 5 resources + tests
- J5-5 🔜 : Audit exhaustif + tag `v0.5.0`

---

### J5-1 ✅ Familles 4, 5, 6 — 7 tools + tests unitaires (2026-05-04)

**Périmètre** :

- `tools/datastore.py` (F4) :
  - `list_datastore_variables` — liste des variables persistantes (MySQL RO, table `dataStore`)
  - `get_datastore_variable` — détail d'une variable (valeur, type, datetime)
- `tools/logs.py` (F5) :
  - `list_log_files` — liste des logs disponibles (réutilise `_core/logs.py`)
  - `tail_log` — tail d'un log Jeedom avec grep optionnel (réutilise `_core/logs.py`)
  - `get_health_summary` — daemons en panne, dépendances KO, messages système, cron en retard (API JSON-RPC)
- `tools/search.py` (F6) :
  - `search_text` — recherche dans noms équipements/commandes/scénarios/expressions (MySQL RO, jointures)
- Tests unitaires pour les 7 tools (mocks DB + logs + API)
- Registration `mcp_server.py` (_register_family4/5/6)

**Livraisons** :

- `_core/logs.py` : + `list_files()` (scan répertoires log, filtre `validate_log_name`, dédup multi-dirs)
- `tools/datastore.py` : `list_datastore_variables(conn, var_type, link_id, key_pattern, limit, offset)`, `get_datastore_variable(conn, key, var_type, link_id)` — MySQL RO, whitelist `dataStore` existante
- `tools/logs.py` : `list_log_files()` (délègue `_core/logs.list_files`), `tail_log(log_name, lines, grep)` (cap 500 lignes), `get_health_summary(conn)` — MySQL RO tables `update`/`message`/`cron`
- `tools/search.py` : `search_text(conn, text, limit)` — 4 requêtes séparées (eqLogic, cmd, scenario, scenarioExpression), min 2 chars, limit 50 par catégorie
- `mcp_server.py` : `_register_family4/5/6` — **25 tools enregistrés**
- Tests : 67 nouveaux tests (19 datastore + 22 logs + 17 search + 9 `list_files` _core) — **557/557 ✅**, couverture 98,20%, ruff propre

---

### J5-2 ✅ `query_sql` + tests unitaires (2026-05-04)

**Périmètre** :

- `tools/query_sql.py` :
  - Parsing `sqlparse` — rejet de tout statement non-SELECT
  - Blacklist tables sensibles : `user`, `session`, `network`, regex `(?i).*creds?|credentials?|password|token.*`
  - LIMIT obligatoire — injecté si absent (50), plafonné à 200
  - Sanitisation runtime systématique sur les résultats (D15.1)
  - D15.3 — refus si le SELECT liste explicitement des colonnes sensibles (password, token, apikey, secret…)
  - Mini SQL cookbook dans la description du tool (mots réservés Jeedom, tables utiles, exemples)
- Tests unitaires exhaustifs : refus INSERT/UPDATE/DELETE/DROP, refus tables blacklistées, LIMIT injecté/plafonné, sanitisation active, D15.3
- Registration `mcp_server.py` — `_register_family7` — **25 tools enregistrés**

**Livraisons** :

- `tools/query_sql.py` : `query_sql(conn, sql)` — 5 fonctions internes (`_check_select_only`, `_extract_table_names`, `_check_blacklist`, `_check_sensitive_columns`, `_ensure_limit`), regex compilées, LIMIT default=50 max=200
- `mcp_server.py` : `_register_family7` ajouté, import `query_sql as query_sql_tools`
- Tests : 69 nouveaux tests — **626/626 ✅**, `query_sql.py` **100% couverture**, couverture globale 98,33%, ruff propre

---

### J5-3 🔜 Tests d'intégration live + corrections schéma

**Périmètre** :

- Tests SSH sur la box réelle (pattern J3-4) pour les 8 nouveaux tools (F4/F5/F6 + `query_sql`) :
  - `tests/integration/tools/test_datastore_live.py`
  - `tests/integration/tools/test_logs_live.py`
  - `tests/integration/tools/test_search_live.py`
  - `tests/integration/tools/test_query_sql_live.py`
- Corrections de schéma si la box révèle des écarts (pattern J3-4)
- Smoke test MCP : `tools/list` = 25 tools

**Sortie attendue** : tous les tests intégration live verts, schéma aligné box réelle.

---

### J5-4 🔜 5 resources + tests

**Périmètre** :

- `resources/overview.py` → wrap `get_install_overview`
- `resources/health.py` → wrap `get_health_summary`
- `resources/scenario.py` → wrap `describe_scenario` + `get_scenario_log`
- `resources/equipment.py` → wrap `get_equipment`
- `resources/logs_today.py` → wrap `tail_log` filtré 24h
- Énumération hybride D6.3 : 2 resources globales statiques + N scénarios/équipements plafonnés + templates `{id}`
- D6.4 — aucune duplication de schéma tool↔resource, wrap strict
- Tests unitaires + smoke test `resources/list` via MCP Inspector

**Sortie attendue** : 5 resources enregistrées, énumération D6.3 implémentée, tests verts.

---

### J5-5 🔜 Audit exhaustif + tag `v0.5.0`

**Méthode** : même grille que J3-5 — croisement systématique sur 3 axes.

**Axes d'audit** :

1. **Brief** — D5.3 (spec tools F4-F6), D5.6 (`query_sql` restreint), D6.2-D6.5 (resources), D15.1 (sanitisation), D15.3 (`query_sql` sécurité)
2. **Documentation projet** — ADRs, PLANNING, `skill-coverage-matrix.md` WF1-WF13
3. **Besoins jeedom-audit** — champs attendus par les scripts, couverture WF par les nouveaux tools

**Grille de triage** :

| Couleur | Traitement |
|---|---|
| 🔴 Bug silencieux / sécurité | Fix immédiat dans la session |
| 🟠 Comportement incorrect documenté | Fix si < 30 min, sinon ADR-0007 |
| 🟡 Fonctionnalité manquante prévue | ADR-0007 + ticket ROADMAP |
| 🟢 Divergence bénigne | Docstring ou ADR-0007 |

**Points d'audit spécifiques J5** (absents de J3-5) :

- `query_sql` : refus non-SELECT prouvé, blacklist exhaustive, LIMIT injecté, D15.3 (refus requêtes ciblant `config`/champs sensibles), cookbook présent dans description
- Resources : D6.4 — pas de duplication schéma tool↔resource, D6.3 plafond énumération cohérent
- `get_health_summary` : champs retournés alignés sur appels API JSON-RPC réels de la box

**Sorties** :

- Table écarts (format J3-5 : ID / fichier / écart / fix / statut)
- Bugs critiques corrigés en session
- Déférés documentés dans ADR-0007
- Chiffres avant/après (tests unitaires, intégration, bugs fixés)
- `PROJECT_STATE.md` mis à jour
- Session journal `docs/sessions/YYYY-MM-DD-j5-5-audit-tools.md`
- Tag `v0.5.0`

---

## Décisions tranchées (référence brief)

Toutes les décisions 🟡/🟢 du brief sont tranchées. Voir `docs/sources/00-brief-cadrage.md` §"Tableau récapitulatif des décisions". Résumé des pivots :

- **D2.1** : daemon Python 3.11+, SDK MCP officiel Anthropic
- **D2.2** : PHP enveloppe market uniquement (manifeste, hooks, UI config, callback)
- **D3.1** : Streamable HTTP (spec MCP 2025-03-26+)
- **D4.1-D4.7** : Bearer token par user Jeedom (`User->setOption()`)
- **D4bis.1-D4bis.7** : MySQL via user RO `jeedom_mcp_ro` + logs fichier + API JSON-RPC localhost ; écriture V2+ via API uniquement, jamais SQL
- **D5.1** : lecture seule V1, écriture candidate V2+
- **D5.3** : 25 tools en 6 familles dont `query_sql` restreint + `get_config` dédié
- **D5.5** : stabilité semver V1.x (schémas tools/resources stables)
- **D8.3** : 9 critères de sortie V1.0.0 (dont sanity check PO #5 et doc MkDocs #9)
- **D8.4** : bêta privée 2+ semaines sur box PO avant soumission market en bêta
- **D10.4** : AGPL-3.0 + bascule jeedom-skills MIT→AGPL conditionnée copyright holder unique
- **D10.5** : branche `main` (stable) + `develop` (intégration)
- **D11.8** : isolation totale credentials du repo (non négociable)
- **D15.1** : sanitisation 3 mécanismes cumulés (whitelist + regex + hard-code plugins) + mask + count

---

## Décisions ouvertes (🔵 — à trancher en J0/J1)

| Décision | Jalon | Question | Critères |
|---|---|---|---|
| ~~D1.2~~ | ~~J0~~ | ~~Version spec MCP cible~~ | ✅ **Tranché J1-1** : spec **2025-03-26** (Streamable HTTP) — mcp==1.27.0 |
| ~~D3.2~~ | ~~J0~~ | ~~Port par défaut~~ | ✅ **Tranché J0-2** : port **8765** (libre sur box PO) |
| ~~D4bis.1~~ | ~~J0~~ | ~~Driver MySQL~~ | ✅ **Tranché J0-2** : PyMySQL (confirmé MariaDB 10.x Bookworm) |
| ~~D4bis.2~~ | ~~J0~~ | ~~Création user MySQL RO~~ | ✅ **Tranché J0-2** : `sudo mysql` unix_socket (user jeedom sans CREATE USER global) |
| ~~D2.4~~ | ~~J0~~ | ~~Isolation Python~~ | ✅ **Tranché J0-2** : venv natif Jeedom `resources/python_venv/` |
| ~~D9.1~~ | ~~J0~~ | ~~Libs Python~~ | ✅ **Tranché J0-1** : httpx + sqlparse + structlog — ADR-0002 |
| ~~D10.3~~ | ~~J0~~ | ~~docs/ embarqué vs branche~~ | ✅ **Tranché J0-1** : docs/ dans main — ADR-0014 |
| D10.8 | J0 | Vérification ID `holmesMcp` libre sur market Jeedom + collision marque | Recherche market officielle |
| ~~D11.6~~ | ~~J0~~ | ~~Lint/format Python~~ | ✅ **Tranché J0-1** : ruff — ADR-0002 |
| ~~D12.6~~ | ~~J0~~ | ~~MkDocs Material + CI docs.yml~~ | ✅ **Tranché J0-1** : MkDocs Material — ADR-0014 |
| D12.7 | J0 | Procédure soumission market : étapes manuelles vs automatisables | Vérification API/UI développeur Jeedom |
| ~~D5.8~~ | ~~J1~~ | ~~Matrice couverture skill jeedom-audit~~ | ✅ **Tranché J1-2** : 13/13 WF couverts, 0 ajout requis — `docs/skill-coverage-matrix.md` + ADR-0019 |
| ~~D6.3~~ | ~~J1~~ | ~~Plafond énumération resources~~ | ✅ **Tranché J1-3** : box PO — 217 eqLogics, 6212 cmds, 62 scenarios, 36 objects. Pagination requise pour `cmd` (>1000), optionnelle pour `eqLogic` (217 acceptable). |
| ~~D14.4~~ | ~~J1~~ | ~~UI vue dédiée logs (framework JS)~~ | ✅ **Tranché J1-1** : tableau HTML natif Jeedom + polling AJAX `setInterval` — pas de dépendance JS externe |
| ~~D15.2~~ | ~~J1~~ | ~~Liste hard-codée plugins à filtrer~~ | ✅ **Tranché J1-1** : liste produite dans `_domain/sanitize.py` — 10 plugins les plus installés (jMQTT, Aqara, Zigbee2MQTT, Sonos, Philips Hue, Z-Wave, Netatmo, ecodevices, rfxcom, agenda) |

---

## POC requis avant validation (🟣)

**D2.3 ✅ — Faisabilité daemon Python sur Bookworm** : toutes les hypothèses #1-#7 validées (J0). ADR-0018 accepted. HTTP retenu, plan B abandonné. Aucun POC ouvert.

---

## Goulets d'étranglement actifs

| Goulet | Type | Matière attendue | Jalon | Statut |
|---|---|---|---|---|
| Aucun | — | — | — | — |

*À mettre à jour si un goulet bloque une session.*

---

## Pré-requis externes

| Pré-requis | Responsable | Dépendance | Statut |
|---|---|---|---|
| Vérification copyright holder `jeedom-skills` (D10.4) | PO | J0 (avant relicence) | 🔴 À faire |
| ADR relicence `jeedom-skills` MIT→AGPL | Claude Code (sur repo jeedom-skills) | Après vérification copyright | 🔴 À faire |
| Communication forum annonce conjointe V1.0.0 | PO | J7 (co-événement release) | 🔴 Futur |

---

## Risques actifs surveillés

| Risque | Niveau | Mitigation |
|---|---|---|
| ~~Claude Desktop HTTP non-TLS LAN (D2.3 hypothèse #7)~~ | ~~🔴 Élevé~~ | ✅ Clos J0-3 — HTTP LAN natif via Claude Code, Claude Desktop via mcp-remote |
| `CREATE USER` privilege absent sur install PO (D4bis.2) | 🟡 Moyen | Message clair, détection à l'install |
| ID `holmesMcp` pris sur market (D10.8) | 🟡 Moyen | Vérification J0, alternatives préparées |
| Validateur market Jeedom (critères partiellement publics) | 🟡 Moyen | Pre-submit checklist en J0/J7 |
| Dérive de scope V1 | 🟡 Moyen | Discipline anti-drift D8.2, ROADMAP.md comme exutoire |
| Extras sanitiseur non vérifiés (jMQTT, Alarme, Jeedom Connect, MQTT Manager) | 🟡 Moyen | ADR-0021 : vérification live obligatoire en J6 (D15.6), patch v1.0.x si delta |

---

## ADRs Holmes MCP

| # | Titre | Statut |
|---|---|---|
| ADR-0001 | Architecture Holmes MCP | draft |
| ADR-0002 | Stack technologique | proposed |
| ADR-0003 | Version spec MCP cible V1 | accepted |
| ADR-0004 | Authentification MCP externe | draft |
| ADR-0005 | Canaux d'accès aux données Jeedom | draft |
| ADR-0006 | Périmètre fonctionnel V1 | draft |
| ADR-0007 | Liste des 25 tools V1 | draft |
| ADR-0008 | Liste des 5 resources V1 | draft |
| ADR-0009 | Réutilisation scripts jeedom-audit | draft |
| ADR-0010 | Nom et identité produit | draft |
| ADR-0011 | Licence AGPL-3.0 | draft |
| ADR-0012 | Stratégie de tests | accepted |
| ADR-0013 | Sécurité opérationnelle — credentials | draft |
| ADR-0014 | Distribution market et versioning | proposed |
| ADR-0015 | Modèle opérationnel PO / Claude Code | draft |
| ADR-0016 | Observabilité | draft |
| ADR-0017 | Sanitisation et guardrails | proposed |
| ADR-0018 | Résultat POC D2.3 | accepted |
| ADR-0019 | Couverture skill jeedom-audit D5.8 | accepted |
| ADR-0020 | Holmes MCP projet séparé de jeedom-skills | accepted |
| ADR-0021 | Stratégie adressage et test par plugin (install PO) | accepted |
