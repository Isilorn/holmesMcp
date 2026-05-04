# Session J3-3 — Famille 3 : 7 tools scénarios

**Date** : 2026-05-04  
**Branche** : `develop`  
**Commit** : `3385dca`

---

## Objectif

Implémenter la famille 3 (scénarios) : 7 tools MySQL RO + `_domain/` walker/graph/cmd_refs + `_core/logs`.

---

## Livrables

### `tools/scenarios.py` — 7 tools

| Tool | Canal | Description |
|---|---|---|
| `list_scenarios(group, is_active, limit=100, offset)` | MySQL | Liste paginée filtrable, sanitisée |
| `find_scenarios_advanced(name_contains, group, is_active, trigger_type, limit=50)` | MySQL | Filtres combinables, LIKE %...% |
| `get_scenario(scenario_id)` | MySQL | Détail complet (state, lastLaunch, trigger, group…) |
| `get_scenario_structure(scenario_id, max_depth=3, follow_scenario_calls=0)` | `scenario_walker` | Arbre brut, machine-friendly |
| `describe_scenario(scenario_id)` | `scenario_walker` + `cmd_refs` | LLM-friendly, résolution `#cmdId#` → `#[O][E][C]#` systématique |
| `find_scenario_dependencies(scenario_id)` | `usage_graph` | Graphe callers/callees |
| `get_scenario_log(scenario_id, lines=100)` | `_core/logs` | `scenarioLog/scenario<id>.log`, max 500 lignes |

### `mcp_server.py`

- `_register_family3` ajouté — **18 tools enregistrés** (4 F1 + 7 F2 + 7 F3)
- `log.info('mcp_initialized', families=[1, 2, 3], tools=18)`

### `tests/unit/tools/test_scenarios.py`

- **44 tests** — 445/445 ✅
- Couvre : filtres SQL, caps limites, sanitisation whitelist, résolution cmd_refs, truncated flag, format log_name, cap 500 lignes

---

## Décisions techniques

- `describe_scenario` : collecte de tous les textes du walker en une passe → batch `cmd_refs.resolve()` → substitution via closures `_resolve_text` / `_humanize`. Seuls les champs effectivement modifiés reçoivent un suffixe `_resolved` (pas de bruit dans la réponse).
- `get_scenario_log` : log name format `scenarioLog/scenario{id}.log` — compatible `_LOG_NAME_RE` (alphanumérique + sous-répertoire + point). Max 500 lignes (plus généreux que les tools MySQL, les logs de run peuvent être longs).
- Whitelist scenario (sanitize.py) : `id, name, state, isActive, mode, type, lastLaunch, description, group, order, timeout, trigger, real_trigger` — pas de colonne `configuration` → zéro risque de fuite blob.

---

## Chiffres

| Métrique | Avant J3-3 | Après J3-3 |
|---|---|---|
| Tests unitaires | 401 | 445 |
| Tools enregistrés | 11 | 18 |
| Familles complètes | 2 | 3 |

---

## Prochaine session : J3-4

- `mcp_server.py` : validation smoke test (tools/list via SSH, invocations basiques)
- Tests d'intégration : `tests/integration/tools/` sur box réelle (SSH Claude Code)
- Déploiement daemon : redémarrage + smoke tests 18 tools
- Tag `v0.4.0` si DoD J3-J4 coché
