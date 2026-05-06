# Session J8-1 — Brief de migration jeedom-audit → Holmes MCP

**Date** : 2026-05-06
**Branche** : `develop`
**Commit(s)** : voir ci-dessous

---

## Objectif

Produire le matériel de migration pour le projet Claude Code `jeedom-skills` — un brief d'action autonome lui permettant de migrer `jeedom-audit` pour utiliser Holmes MCP comme source de données exclusive, sans intervention du projet holmesMcp.

Le projet jeedom-skills était jusqu'ici identifié comme destinataire de la migration (ADR-0019/0020), mais aucun document actionnable n'existait. Les analyses produites précédemment (J8-audit, J7bis-2) étaient orientées Holmes MCP — pas jeedom-skills.

---

## Livrables

| Fichier | Ce qui a été produit |
|---------|---------------------|
| `docs/sources/migration-jeedom-audit-brief.md` | Brief de migration complet — 10 sections, destiné au projet jeedom-skills Claude Code |

---

## Contenu du brief (structure)

1. **Contexte et objectif** — Pourquoi migrer, ce qui change, ce qui reste, périmètre branche `develop`
2. **Inventaire composants** — Tableau Éliminer / Transformer / Conserver avec chemins exacts pour chaque fichier de `jeedom-audit/`
3. **Connexion à Holmes MCP** — Format `.mcp.json` Claude Code, Bearer token, pré-requis utilisateur, remplacement de `version_check.py`
4. **Mapping WF → outils Holmes MCP** — Pour chacun des 13 WF, tableau "ancienne approche → nouvel appel Holmes MCP"
5. **Contraintes techniques `query_sql()`** — LIMIT auto-injectée, backticks, blacklist tables, colonnes sensibles, format de retour
6. **SQL cookbook de substitution** — 8 requêtes sans outil Holmes MCP dédié, toutes validées MariaDB, avec LIMIT explicite
7. **Réécriture SKILL.md section par section** — §3, §Routage (supprimer), §6 Gotchas, §7 scripts→outils, §9 Index
8. **Gotcha post-migration `describe_scenario()`** — Remplacement en une passe de walker + resolve_cmd_refs
9. **Checklist de validation** — 11 items, définition de "testable"
10. **Documents de référence Holmes MCP** — Pointeurs vers les sources d'autorité

---

## Périmètre du brief

Le brief couvre la migration de `jeedom-audit` sur branche `develop` de `jeedom-skills`. Il ne couvre pas :

- La création de nouveaux outils Holmes MCP
- La modification de Holmes MCP
- Les autres skills de `jeedom-skills`

---

## Résultats qualité

| Métrique | Valeur |
|----------|--------|
| Tests unitaires | N/A (aucun Python modifié) |
| Ruff | N/A |
| Déploiement box | N/A |

---

## Prochaine étape J8

**Axe 1 — Bêta privée** : sessions Claude Code réelles sur Holmes MCP par le PO (activité PO — 5 sessions min, 2+ semaines).

**Axe 2 — Migration jeedom-skills** : le projet Claude Code `jeedom-skills` peut démarrer la migration depuis `docs/sources/migration-jeedom-audit-brief.md`.
