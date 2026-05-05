# Matrice de couverture — skill jeedom-audit ↔ Holmes MCP V1

> **Livrable D5.8** — Produit en J1-2 (2026-05-03).  
> Référence jeedom-audit : commit `a792179` (tag `v1.0.1`, branche `main`).  
> Référence Holmes MCP : liste des 25 tools D5.3, brief `docs/sources/00-brief-cadrage.md`.

---

## 1. Synthèse

| Indicateur | Valeur |
|---|---|
| Workflows jeedom-audit analysés | WF1–WF13 (13 workflows) |
| Workflows couverts à 100 % | **13 / 13** |
| Workflows couverts partiellement | 0 |
| Workflows non couverts | 0 |
| Tools Holmes MCP V1 suffisants | **Oui — les 25 tools couvrent tout** |
| Nouveaux tools requis | **Aucun** |
| Bascule jeedom-audit → Holmes MCP | ✅ Faisable sans perte de capacité |

**Conclusion :** la liste D5.3 couvre l'intégralité des workflows WF1–WF13 de jeedom-audit.  
La bascule de jeedom-audit en consommatrice Holmes MCP (D5.8) est validée sans ajout de périmètre V1.

---

## 2. Tableau de mapping WF ↔ tools

### WF1 — Audit général

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Version + config système | SQL `config` WHERE plugin='core' | `get_config` (namespace='core') + `get_install_overview` |
| Plugins + mises à jour | SQL `` `update` `` + `plugin::listPlugin` | `list_plugins` + `query_sql` (update table) |
| Équipements actifs / désactivés | SQL `eqLogic` | `list_equipments` + `find_equipments_advanced` |
| Scénarios actifs / inactifs / modes | SQL `scenario` | `list_scenarios` |
| Commandes mortes | SQL JOIN `cmd` ↔ `eqLogic` | `query_sql` |
| Variables dataStore | SQL `dataStore` | `list_datastore_variables` |
| Messages système + daemons + cron | SQL `message` + API | `get_health_summary` |
| Qualité historique | SQL `history` GROUP BY | `query_sql` |
| Logs core/php | SSH `tail` logs | `tail_log` |

**Couverture : ✅ Totale**

---

### WF2 — Diagnostic scénario

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Résolution + désambiguïsation | SQL `scenario` fuzzy | `find_scenarios_advanced` |
| Arbre scénario (scenario_tree_walker) | `scenario_tree_walker.py` | `get_scenario_structure` |
| État runtime (lastLaunch, state) | API `scenario::byId` | `get_scenario` (inclut lastLaunch + state) |
| Triggers + valeurs courantes | SQL `cmd` + API `cmd::byId` | `find_commands_advanced` (currentValue) |
| Log scénario récent | SSH `scenarioLog/N` | `get_scenario_log` + `tail_log` |
| Résolution `#ID#` dans expressions | `resolve_cmd_refs.py` | `describe_scenario` (résolution intégrée) |
| Vérification format schedule | SQL `scenario.trigger` | `get_scenario` (champ trigger) |

**Couverture : ✅ Totale**

---

### WF3 — Diagnostic équipement

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Résolution équipement par nom | SQL fuzzy `eqLogic` | `find_equipment_by_name` |
| Détail (status, isEnable, config) | SQL `eqLogic` + `cmd` | `get_equipment` |
| État daemon du plugin | API `plugin::listPlugin` | `get_health_summary` |
| Dernière valeur + historique | SQL `cmd.value` + `history` | `find_commands_advanced` + `get_command_history` |
| Logs plugin | SSH `tail` log plugin | `tail_log` |

**Couverture : ✅ Totale**

---

### WF4 — Diagnostic plugin

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Identification plugin | SQL `` `update` `` + API | `list_plugins` |
| État daemon + dépendances | API `plugin::listPlugin` | `get_health_summary` |
| eqLogics du plugin (actifs / warning) | SQL `eqLogic` WHERE eqType_name | `find_equipments_advanced` (filtre plugin) |
| Logs plugin + dep | SSH `tail` | `tail_log` (log plugin + `<plugin>_dep`) |

**Couverture : ✅ Totale**

---

### WF5 — Explication scénario

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Résolution scénario | SQL fuzzy | `find_scenarios_advanced` |
| Arbre récursif (scenario_tree_walker) | `scenario_tree_walker.py` | `get_scenario_structure` |
| Résolution `#ID#` systématique | `resolve_cmd_refs.py` | `describe_scenario` (résolution intégrée) |
| Pseudo-code IF/THEN/ELSE lisible | Construction Claude | `describe_scenario` (format UI Jeedom) |
| Appels inter-scénarios (follow_calls) | `follow_scenario_calls=2-3` | `get_scenario_structure` (follow_scenario_calls param) |

**Couverture : ✅ Totale** — `describe_scenario` remplace avantageusement la combinaison scenario_tree_walker + resolve_cmd_refs + construction Claude

---

### WF6 — Graphe d'usage

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Identification cible (cmd/eqLogic/scenario) | SQL + fuzzy | `find_equipment_by_name` / `find_commands_advanced` / `find_scenarios_advanced` |
| Graphe d'usage cmd → scénarios (triggers/conditions/actions/dataStore) | `usage_graph.py` | `find_command_usages` (livré J7bis-1) |
| Graphe d'usage scenario → scenarios | `usage_graph.py` | `find_scenario_dependencies` |
| Résolution #ID# dans résultats | `resolve_cmd_refs.py` | `describe_scenario` (si contexte scénario) |

**Couverture : ✅ Totale** — `find_command_usages` + `find_scenario_dependencies` couvrent les deux axes de usage_graph.py. Mis à jour J7bis-2 (l'audit J8-audit avait identifié un gap cmd→scénarios, résolu par `find_command_usages`).

---

### WF7 — Suggestions de refactor

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Audit structurel de base | WF1 composé | WF1 Holmes MCP (composition de tools) |
| Explication scénario cible | WF5 composé | `describe_scenario` + `get_scenario_structure` |
| Conditions dupliquées | Analyse structure | `get_scenario_structure` |
| Délais en dur / triggerId() déprécié | Analyse expressions | `get_scenario_structure` |
| Commandes sans Type Générique | SQL `cmd.generic_type IS NULL` | `find_commands_advanced` (filtre generic_type) |
| Scénarios désactivés référencés | SQL + usage_graph | `find_scenarios_advanced` + `find_scenario_dependencies` |
| Variables orphelines | SQL dataStore + expressions | `list_datastore_variables` + `find_scenarios_advanced` |

**Couverture : ✅ Totale** — WF7 est une composition de WF1+WF5, entièrement couverte

---

### WF8 — Valeur courante d'une commande

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Résolution commande par nom | SQL fuzzy `cmd` JOIN `eqLogic` | `find_commands_advanced` + `find_equipment_by_name` |
| Valeur courante (runtime) | API `cmd::byId` (currentValue) | `list_commands(equipment_id)` ou `get_equipment(equipment_id)` — champ `currentValue` enrichi via API JSON-RPC |

> **Note** (J3-5) : `find_commands_advanced` ne retourne pas `currentValue` — enrichissement API non applicable sur les listes transverses (coût N×API prohibitif). Pour `currentValue`, résoudre d'abord l'`equipment_id` via `find_commands_advanced`, puis appeler `list_commands(equipment_id)` ou `get_equipment(equipment_id)`.

**Couverture : ✅ Totale** (via composition find_commands_advanced → list_commands)

---

### WF9 — Historique d'une commande

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Résolution commande | SQL fuzzy | `find_commands_advanced` |
| Historique live + archivé | API `cmd::getHistory` + SQL `history` | `get_command_history` |

**Couverture : ✅ Totale**

---

### WF10 — Variable dataStore

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Liste variables globales / locales | SQL `dataStore` | `list_datastore_variables` |
| Valeur + portée (globale/locale) | SQL `dataStore.link_id` | `get_datastore_variable` |

**Couverture : ✅ Totale**

---

### WF11 — Recherche libre

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Recherche par nom équipement | SQL LIKE fuzzy | `find_equipments_advanced` + `search_text` |
| Recherche par nom commande | SQL LIKE fuzzy | `find_commands_advanced` + `search_text` |
| Recherche dans expressions scénario | SQL LIKE `scenarioExpression` | `search_text` (périmètre cross-entités) |

**Couverture : ✅ Totale** — `search_text` est conçu exactement pour ce cas d'usage

---

### WF12 — Cartographie d'orchestration

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Point d'entrée | SQL fuzzy | `find_scenarios_advanced` |
| Arbre récursif (follow_scenario_calls=3, anti-cycle) | `scenario_tree_walker.py` | `get_scenario_structure` (follow_scenario_calls=3) |
| Annotations avec résolution #ID# | `resolve_cmd_refs.py` | `describe_scenario` |
| Sortie prose ≤10 nœuds / mermaid >10 nœuds | Construction Claude | Construction Claude (données issues des tools ci-dessus) |

**Couverture : ✅ Totale**

---

### WF13 — Forensique causale

| Étape | Canal jeedom-audit | Tool Holmes MCP V1 |
|---|---|---|
| Indices initiaux | SQL + API | `find_scenarios_advanced` + `find_commands_advanced` |
| Graphe d'usage depuis point d'arrivée | `usage_graph.py` | `find_scenario_dependencies` |
| Logs sur fenêtre temporelle | SSH `tail` + grep | `tail_log` (N lignes + grep) |
| Remontée triggers ascendante (max 5 niveaux) | Multi-pass `usage_graph.py` | Multi-pass `find_scenario_dependencies` + `get_scenario_structure` |
| Cause racine + suggestions | Construction Claude | Construction Claude |

**Couverture : ✅ Totale** — requiert `tail_log` (logs obligatoires — aucun fallback en mode sans logs)

---

## 3. Analyse des écarts

### 3.1 Fonctions jeedom-audit sans équivalent direct — mais couvertes autrement

| Fonction jeedom-audit | Approche jeedom-audit | Couverture Holmes MCP |
|---|---|---|
| `resolve_cmd_refs.py` (résolution batch #ID#) | Script dédié SSH+SQL | Intégré dans `describe_scenario` ; pour SQL ad-hoc, `find_commands_advanced` par ID |
| `router.py` (MySQL vs API auto) | Routage transparent selon disponibilité | **Inutile** — le daemon Holmes MCP est sur la box, les deux canaux sont toujours disponibles simultanément |
| `version_check.py` (vérification version au démarrage) | Script startup dédié | `get_config` (key='version', plugin='core') — vérification à la demande |
| SSH `~/.my.cnf` / `credentials.json` | Gestion credentials côté client | **Inutile** — auth Bearer côté client, credentials MySQL côté daemon dans `/etc/holmes_mcp_ro.conf` |

### 3.2 Amélioration nette par rapport à jeedom-audit

- **Résolution `#ID#` intégrée** dans `describe_scenario` : pas besoin d'un script séparé — les outils Holmes MCP retournent directement les noms lisibles.
- **Accès simultané MySQL + API** sans routage : le daemon est sur la box, les deux canaux sont toujours disponibles. La notion de "mode API-only" de jeedom-audit disparaît.
- **`get_health_summary`** consolide ce que jeedom-audit obtenait en 3 canaux séparés (API `plugin::listPlugin`, SQL `message`, API cron).
- **Setup utilisateur simplifié** : l'utilisateur final ne configure ni SSH ni credentials MySQL — juste une URL + token Bearer dans son client MCP.

---

## 4. Scripts jeedom-audit → modules Holmes MCP

| Script jeedom-audit | Module Holmes MCP | Statut |
|---|---|---|
| `db_query.py` | `_core/db.py` | ✅ Implémenté J1-1 |
| `api_call.py` | `_core/api.py` | ✅ Implémenté J1-1 |
| `logs_query.py` | `_core/logs.py` | ✅ Implémenté J1-1 |
| `resolve_cmd_refs.py` | Intégré dans `describe_scenario` (tool J4) | ⏳ J4 |
| `scenario_tree_walker.py` | `_domain/scenario_walker.py` + tools J3 | ⏳ J3 |
| `usage_graph.py` | `_domain/usage_graph.py` + tool J5 | ⏳ J5 |
| `_common/sensitive_fields.py` | `_domain/sanitize.py` | ⏳ J2 |
| `_common/router.py` | **Non porté** — inutile (daemon sur la box) | N/A |
| `_common/version_check.py` | **Non porté** — `get_config` suffit | N/A |

---

## 5. Référence jeedom-audit

- **Commit de référence :** `a792179` (`jeedom-skills` main, tag `v1.0.1`)
- **Fichiers analysés :** `SKILL.md`, `references/audit-templates.md`, `references/sql-cookbook.md`
- **Workflows analysés :** WF1–WF13 (§7 de SKILL.md)
- **Date d'analyse :** 2026-05-03 (J1-2)

> Cette matrice se rapporte à jeedom-audit `v1.0.1`. Si jeedom-audit évolue (nouveaux WF, nouveaux scripts),  
> mettre à jour cette matrice et, si un gap apparaît, rédiger une ADR amendant D5.3.
