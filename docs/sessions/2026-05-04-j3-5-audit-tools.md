# Session J3-5 — Audit exhaustif 18 tools Holmes MCP

**Date** : 2026-05-04  
**Branche** : `develop`  
**Commit** : `4927640`

---

## Objectif

Croiser les 18 tools implémentés (J3-J4 + J3-4bis) contre :
1. Brief D5.3, D4bis.6, D15.1 — spec tools, routing, sanitisation
2. Documentation projet (ADRs, PLANNING, skill-coverage-matrix)
3. Besoins jeedom-audit WF1-WF13 — champs attendus par les scripts

---

## Écarts identifiés et traitement

### Bugs critiques corrigés

| ID | Fichier | Écart | Fix |
|---|---|---|---|
| E01 | `sanitize.py` | `position` masqué `***FILTERED***` dans `list_objects` — whitelist `object` avait `order` au lieu de `position` depuis J3-4 | `order`/`image` → `position` dans `_TABLE_WHITELISTS['object']` |
| E06 | `sanitize.py` | `currentValue`/`collectDate` injectés post-sanitize, hors whitelist `cmd` (D15.1) | Ajout au whitelist `cmd` |
| E07 | `sanitize.py` | `id` stale dans whitelists `history`/`historyArch` (supprimé du SELECT en J3-4) | `id` retiré des deux whitelists |
| E02 | `discovery.py` | `get_config` — `plugin` requis alors que D5.6.bis dit optionnel + `*` wildcard absent | `plugin: str \| None = None`, si None ou `*` → tous namespaces |
| E03 | `scenarios.py` | `find_scenarios_advanced` — filtre `mode` absent (MySQL dispo dans `_SCEN_COLS`) | Paramètre `mode: str \| None = None` ajouté |

### Documentation et déférés

| ID | Écart | Traitement |
|---|---|---|
| E04 | `find_commands_advanced` sans `currentValue` — WF8 skill-coverage-matrix incorrect | Matrix WF8 mise à jour : redirection vers `list_commands`/`get_equipment` |
| E05 | `get_command_history` via MySQL vs D4bis.6 (API JSON-RPC pour history récente) | Note ADR-0007 — décision assumée, tests intégration validés |
| E08 | `find_scenario_dependencies` — description "bidirectionnel" incorrecte (callers only) | Docstrings corrigées (`mcp_server.py` + `scenarios.py`) |
| E09 | `find_equipments_advanced` — `dernier seen` (runtime) + `historisation` (attribut cmd) absents | Note ADR-0007 + V1.x tickets |
| E10 | `find_scenarios_advanced` — 3 filtres absents (`dernière exécution`, `contient commande`, `mots-clés`) | Note ADR-0007 + V1.x tickets |
| E11 | `get_scenario` — log séparé en `get_scenario_log` vs brief | Cross-ref docstring + note ADR-0007 |
| E12 | `get_config` — paramètre `plugin` vs `namespace` (brief) | Note ADR-0007 — divergence acceptée |

---

## Chiffres

| Métrique | Avant J3-5 | Après J3-5 |
|---|---|---|
| Tests unitaires | 476 | 490 (+14) |
| Tests intégration live | 93 | 93 (tous passés) |
| Bugs sanitisation corrigés | — | 3 (E01, E06, E07) |
| Fonctionnalités ajoutées | — | 2 (get_config optionnel, filtre mode) |
| Notes ADR-0007 | — | 7 déférés documentés |

---

## Prochaine session : J5

7 tools restants (F4-F6 + query_sql) + 5 resources minimales :
- `list_datastore_variables`, `get_datastore_variable`
- `tail_log`, `list_log_files`, `get_health_summary`
- `search_text`
- `query_sql` (SELECT-only, blacklist tables, LIMIT obligatoire, mini SQL cookbook)
- 5 resources `jeedom://install/overview`, `jeedom://install/health`, `jeedom://scenario/{id}`, `jeedom://equipment/{id}`, `jeedom://logs/today`
