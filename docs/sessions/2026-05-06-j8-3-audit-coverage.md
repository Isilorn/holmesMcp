# Session J8-3 — Audit couverture jeedom-audit × Holmes MCP v1.2.0

**Date** : 2026-05-06
**Branche** : `develop`
**Commit(s)** : à produire en fin de session

---

## Objectif

Auditer la couverture des 13 WF jeedom-audit avec Holmes MCP v1.2.0 (27 tools), confirmer que les 8 requêtes SQL du cookbook de migration (A–H) sont bien réduites au minimum, et mettre à jour les documents de référence.

Session documentation/analyse — aucun SSH ni déploiement.

---

## Résultats : tableau 13 WF × verdict v1.2.0

| WF | Titre | Couverture | Évolution v1.1.1 → v1.2.0 |
|---|---|---|---|
| WF1 | Audit général | ✅ Totale | `get_health_summary` étendu (dead_commands + historized_cmds_without_data) ; `find_equipments_advanced(has_warning=True)` — 3 requêtes cookbook éliminées (B, E, F) |
| WF2 | Diagnostic scénario | ✅ Totale | Inchangé |
| WF3 | Diagnostic équipement | ✅ Totale | `find_equipments_advanced(has_warning=True)` améliore la détection warning |
| WF4 | Diagnostic plugin | ✅ Totale | `find_equipments_advanced(has_warning=True)` clarifie le filtre warning |
| WF5 | Explication scénario | ✅ Totale | Inchangé |
| WF6 | Graphe d'usage | ✅ Totale | `find_equipment_usages(equipment_id)` comble l'axe eqLogic→scénarios — cookbook §A obsolète |
| WF7 | Suggestions de refactor | ✅ Totale | `list_datastore_variables(orphaned=True)` + `find_commands_advanced(generic_type_missing=True)` + `find_scenarios_advanced(called_while_inactive=True)` — 3 requêtes cookbook éliminées (C, D, G) |
| WF8 | Valeur courante | ✅ Totale | Inchangé |
| WF9 | Historique | ✅ Totale | Inchangé |
| WF10 | Variable dataStore | ✅ Totale | `list_datastore_variables(orphaned=True)` améliore la détection d'orphelins |
| WF11 | Recherche libre | ✅ Totale | Inchangé |
| WF12 | Cartographie d'orchestration | ✅ Totale | Inchangé |
| WF13 | Forensique causale | ✅ Totale | Inchangé |

**13/13 WF couverts. 0 gap résiduel.**

---

## Audit cookbook A–H

### Résultat

| Recette | WF | Description | Statut v1.2.0 | Outil de substitution |
|---|---|---|---|---|
| A | WF6 | Graphe d'usage eqLogic → scénarios | ✅ **OBSOLÈTE** | `find_equipment_usages(equipment_id)` |
| B | WF1 | Commandes mortes | ✅ **OBSOLÈTE** | `get_health_summary()` → `dead_commands` |
| C | WF7 | Variables dataStore orphelines | ✅ **OBSOLÈTE** | `list_datastore_variables(orphaned=True)` |
| D | WF7 | Commandes sans Type Générique | ✅ **OBSOLÈTE** | `find_commands_advanced(generic_type_missing=True)` |
| E | WF1 | Qualité historique (cmds info sans donnée) | ✅ **OBSOLÈTE** | `get_health_summary()` → `summary.historized_cmds_without_data` |
| F | WF1/WF3 | Équipements en warning ou danger | ✅ **OBSOLÈTE** | `find_equipments_advanced(has_warning=True)` |
| G | WF7 | Scénarios désactivés mais appelés | ✅ **OBSOLÈTE** | `find_scenarios_advanced(called_while_inactive=True)` |
| H | WF1 | Plugins avec mises à jour (remoteVersion) | ✅ **OBSOLÈTE** | `list_plugins()` — champ `remote_version` ajouté, filtrer `state != 'ok'` |

**8/8 recettes obsolétées. Cookbook vide.**

### Note sur H

`list_plugins()` expose désormais `remote_version` (= `remoteVersion` DB). Un seul appel suffit pour voir tous les plugins avec leur version installée, leur version distante et leur état — le LLM filtre client-side par `state != 'ok'`.

---

## Documents mis à jour

| Fichier | Modifications |
|---|---|
| `docs/skill-coverage-matrix.md` | Header v1.2.0 ; WF1 : ajout `has_warning=True` + dead_commands + historized ; WF4 : `has_warning=True` ; WF6 : axe eqLogic + `find_equipment_usages` ; WF7 : `orphaned`, `generic_type_missing`, `called_while_inactive` ; §3.2 : note 7/8 cookbook |
| `docs/sources/migration-jeedom-audit-brief.md` | Header v1.2.0 ; §4 WF1 : 3 lignes query_sql → outils dédiés ; §4 WF6 : eqLogic → `find_equipment_usages` ; §4 WF7 : tableau des 3 nouveaux outils ; §6 : recettes A–G remplacées par tableau de substitution, seule H conservée |

---

## Résultats qualité

| Métrique | Valeur |
|---|---|
| Tests unitaires | N/A (aucun Python modifié) |
| Ruff | N/A |
| Déploiement box | N/A |

---

## Prochaine sous-session : J8-4

Audit live — exécuter les 13 WF sur la box réelle avec Holmes MCP v1.2.0 depuis Claude Code, valider la couverture opérationnelle, et produire un rapport de bêta.
