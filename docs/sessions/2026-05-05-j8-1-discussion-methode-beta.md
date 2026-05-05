# Session J8-1 — Discussion méthode bêta privée

**Date** : 2026-05-05
**Branche** : `develop`
**Commit(s)** : aucun code — session discussion + documentation

---

## Objectif

Trancher la méthodologie de la bêta privée J8 : client MCP retenu, approche de validation, et décision sur les prérequis avant de démarrer les sessions de test.

---

## Livrables

| Fichier | Ce qui a changé |
| --- | --- |
| `docs/PLANNING.md` | Section J7bis insérée (4 items pré-migration) ; J8 mis à jour (client tranché, DoD migration jeedom-audit) |
| `docs/state/PROJECT_STATE.md` | Header mis à jour (jalon en cours = J7bis) ; section J7bis avec DoD ajoutée |
| `docs/sessions/2026-05-05-j8-audit-migration-jeedom-skill.md` | Session record de l'audit gap analysis (produit en session parallèle) |
| `docs/skill-migration-audit-playbook.md` | Playbook réutilisable audit migration skill → Holmes MCP |

---

## Décisions prises en session

**Client bêta retenu : Claude Code** (HTTP LAN natif, déjà validé J0-3). Claude Desktop écarté (pas de support HTTP LAN natif, nécessiterait mcp-remote). Gemini Advanced (Google One AI Pro) écarté (pas un client MCP). MCP Inspector retenu comme outil de debug complémentaire.

**Méthodologie bêta J8** : double axe — (1) sessions Claude Code directes sur Holmes MCP, (2) migration jeedom-audit (branche `develop` sur `jeedom-skills`) pour validation bout-en-bout conforme à ADR-0019/0020.

**Jalon J7bis créé** : 4 améliorations Holmes MCP identifiées dans l'audit de migration, traitées avant la bêta pour garantir la qualité de l'expérience client — outil `find_command_usages`, doc LIMIT query_sql, auto-backtick mots réservés, FAQ Jeedom 4.4.x. Version cible `1.1.0`.

**Architecture jeedom-skills clarifiée** : `jeedom-skills` est un repository hébergeant plusieurs skills. Actuellement : `jeedom-audit` (SSH + MySQL directs). Prévu : `jeedom-plugins` (non démarré).

---

## Résultats qualité

| Métrique | Valeur |
| --- | --- |
| Tests unitaires | N/A (aucun Python modifié) |
| Ruff | N/A |
| Déploiement box | N/A |

---

## Incidents / anomalies

Aucun.

---

## Prochaine sous-session : J7bis-1

**Objectif** : Implémenter `find_command_usages(cmd_id)`, auto-backtick mots réservés dans `query_sql`, documenter comportement LIMIT, FAQ Jeedom 4.4.x — version `1.1.0`
**Pré-requis** : Snapshot Proxmox avant déploiement sur box (tests d'intégration live)
