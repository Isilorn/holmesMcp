# Session J2-2 — `_domain/usage_graph.py` + `_domain/scenario_walker.py`

**Date** : 2026-05-04  
**Durée estimée** : 1 session  
**Branche** : `main`

---

## Objectif

Implémenter `_domain/usage_graph.py` et `_domain/scenario_walker.py`, portés depuis les scripts jeedom-audit (`docs/sources/jeedom-audit-scripts/`), avec 100% de couverture de tests.

---

## Livraisons

### `_domain/usage_graph.py`

Port de `jeedom-audit/usage_graph.py`. API publique :

```python
resolve(target_type: str, target_id: int, conn) -> dict
```

- `target_type` : `'cmd'` | `'eqLogic'` | `'scenario'`
- Déduplication triggers/conditions/actions inter-commandes pour cible eqLogic
- `false_positive_warnings` pour les blocs PHP `code`
- Retourne `{'error': ...}` si cible introuvable ou type inconnu

Adaptations vs source :
- `db_query.run(sql, params, creds)` → `db.query(conn, sql, params)` (PyMySQL local)
- Placeholders `?` → `%s` (PyMySQL)
- Pas de `main()` / stdin-stdout — module bibliothèque pur

### `_domain/scenario_walker.py`

Port de `jeedom-audit/scenario_tree_walker.py`. API publique :

```python
walk(scenario_id: int, conn, max_depth=3, follow_scenario_calls=0,
     _visited_scenarios=None) -> dict
```

- Parcours récursif (max_depth=3 par défaut)
- Anti-cycle inter-scénarios via `_visited_scenarios`
- Troncature à 100 sous-éléments avec avertissement
- Suivi des appels `scenario/start` jusqu'à `follow_scenario_calls` niveaux
- Retourne `{'error': ..., 'scenario': None, 'tree': [], ...}` si scénario introuvable

Adaptations vs source :
- `%s` placeholders pour PyMySQL (IN clause : `%s, %s, ...` dynamique)
- `_child_element_ids` simplifié : utilise `type` uniquement (après `_group_by_element`)
- Pas de `main()` / stdin-stdout

### Tests

| Fichier | Tests | Couverture |
|---|---|---|
| `test_usage_graph.py` | 30 | 100% |
| `test_scenario_walker.py` | 49 | 100% |
| **Total session J2-2** | **79** | — |
| **Total unitaires cumulé** | **311** | — |

---

## Résultats

```
311 passed in 2.98s
usage_graph.py   : 100%
scenario_walker.py : 100%
sanitize.py      : 100%
Couverture globale : 85%
```

Ruff : aucune erreur.

---

## Prochaine session : J2-3

- `_domain/cmd_refs.py` (résolveur `#ID#` → `#[O][E][C]#`, cache de session)
- Intégration des 3 modules `_domain/` dans `mcp_server.py` (stub)
- ADR-0017 proposed (couverture tests _domain/)
- Tag `v0.3.0` + merge
