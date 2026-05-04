# Session — Audit de cohérence doc + formalisation process (2026-05-04)

**Jalon** : transverse (hors Jx)
**Type** : Audit + corrections doc + process (pas de SSH)
**Durée** : ~1 session Claude Code

---

## Objectif de la session

Vérification exhaustive de la cohérence entre code, ADRs, mémoire et état du projet. Correction de toutes les dérives identifiées. Formalisation des règles pour éviter la récurrence.

---

## Écarts corrigés

### Erreurs factuelles

| Fichier | Problème | Correction |
|---|---|---|
| ADR-0003 | Jamais remplie malgré D1.2 tranché en J1-1 | Réécrite et acceptée (spec 2025-03-26, mcp==1.27.0) |
| ADR-0004 | Token stocké via `User->setOption()` — faux | Corrigé : `config::save('token_<user_id>', token, __CLASS__)` |
| ADR-0015 | User SSH `jeedom` | Corrigé : `gtillit` |

### Incohérences entre documents

| Fichier | Problème | Correction |
|---|---|---|
| ADR-0009 | `_domain/cmd_refs.py` planifié comme module séparé | Aligné sur ADR-0019 : intégré dans `describe_scenario` |
| ADR-0017 | 8 plugins (liste initiale) | Mis à jour : 10 plugins D15.2 (jMQTT, Aqara, Zigbee2MQTT, Sonos, Philips Hue, Z-Wave, Netatmo, ecodevices, rfxcom, agenda) |
| PLANNING.md §4.3 critère #4 | "Claude Desktop" comme client de validation V1 | Aligné sur ADR-0018 : "Claude Code + MCP Inspector" |

### Obsolescences

| Fichier | Problème | Correction |
|---|---|---|
| ADR-0002 | D4bis.1 "à confirmer J0-2", structlog "à intégrer J1" | Décisions marquées confirmées/faites |
| ADR-0007 | "La liste sera raffinée en J1" | D5.8 settled via ADR-0019 noté |
| memory/reference_key_files.md | 17 ADRs | Corrigé : 19 ADRs |

### Manques

| Manque | Correction |
|---|---|
| Fichiers session J1-1 et J1-2 absents | Créés : `2026-05-03-j1-1-core-tests.md` + `2026-05-03-j1-2-skill-coverage.md` |
| Tag `v0.1.0` sur mauvais commit | Déplacé sur `2359277` (dernier commit J0) |
| Tag `v0.2.0` prématuré | Supprimé — sera posé quand J1 DoD est coché |

---

## Règles process formalisées

Ajoutées dans `docs/state/CONTRIBUTING-CLAUDE-CODE.md` §3 et `docs/README.md` :

1. **ADR on commit** : toute implémentation met à jour son ADR dans le même commit
2. **Début de jalon** : planifier les sous-sessions dans PROJECT_STATE.md avant de commencer
3. **Fin de sous-session** (pas fin de session Claude Code) : ADRs + session file + PROJECT_STATE + commit
4. **Fin de jalon** : DoD coché ligne par ligne + tag
5. **Stratégie branches** : `develop` pour le code en cours, `main` = dernier jalon stable, merge uniquement à la fin d'un jalon DoD coché

---

## État git en fin de session

| Ref | Commit | Description |
|---|---|---|
| HEAD / main / develop | `cba0b93` | process: documente la stratégie develop vs main |
| tag `v0.1.0` | `2359277` | Fin J0 (chore: add Claude Code project settings) |
| tag `v0.2.0` | — | Absent — à créer quand J1 complet |

---

## Actions SSH réalisées

Aucune — session 100% offline.

---

## Prochaine session : J1-3 (SSH requis)

**Pré-requis PO** : snapshot Proxmox avant de commencer.

Contenu groupé :
- Fixtures synthétiques `tests/fixtures/synthetic/` + tests d'intégration `tests/integration/` (offline mais groupés)
- D6.3 : mesure empirique plafond resources sur box
- Tests intégration `_core/` sur box réelle
- Redéploiement daemon avec nouvelle version
