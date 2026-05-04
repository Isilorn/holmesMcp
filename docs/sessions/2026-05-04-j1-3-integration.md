# Session J1-3 — Tests d'intégration + D6.3

**Date** : 2026-05-04
**Statut** : ✅ Terminée

## Objectifs

- Fixtures synthétiques `tests/fixtures/synthetic/`
- Tests d'intégration `tests/integration/` sur box réelle
- D6.3 : mesure empirique du plafond resources
- Déploiement daemon mis à jour

## Réalisé

### Fixtures synthétiques

- `config_tokens.json` : 2 tokens synthétiques (format résultat `_TOKEN_QUERY`)
- `eqlogics.json` : 5 équipements (philipsHue, Zigbee2Mqtt, Netatmo, Aqara, rfxcom)
- `log_sample.txt` : 10 lignes de log Jeedom formatées
- `tests/conftest.py` : fixtures pytest `synthetic_tokens`, `synthetic_eqlogics`, `synthetic_log_path`

### Tests d'intégration (18 passed, 1 skipped)

| Fichier | Tests | Résultat |
|---|---|---|
| `test_db_live.py` | connect, select1, tables, comptages D6.3 | 7/7 ✅ |
| `test_auth_live.py` | TokenStore.from_db, resolve_unknown | 2/2 ✅ |
| `test_api_live.py` | blacklist ×2, version, eqlogic::all | 3/3 + 1 skip (crypt:) |
| `test_logs_live.py` | resolve, tail, grep, validations ×3 | 6/6 ✅ |

### Bugs corrigés dans _core/db.py

**Bug 1 — Socket unix** : `_DB_HOST = 'localhost'` → PyMySQL connectait en TCP `127.0.0.1`, refusé par MariaDB (user GRANT @localhost = socket). Corrigé : `unix_socket='/run/mysqld/mysqld.sock'`, configurable via `socket=` dans le conf.

**Bug 2 — params vide + LIKE** : `cur.execute(sql, ())` → PyMySQL formatait `%_` dans `LIKE 'token_%'` → `TypeError`. Corrigé : passer `None` au lieu de `()` quand params est vide.

### D6.3 — Mesure empirique box PO

| Entité | Nombre |
|---|---|
| eqLogic | 217 |
| cmd | 6 212 |
| scenario | 62 |
| object | 36 |

**Décision** : pagination requise pour `cmd` (>1000 items). `eqLogic` (217) acceptable sans pagination en V1. `scenario` et `object` bien en dessous du seuil.

### Clé API chiffrée (crypt:)

La clé API Jeedom est stockée chiffrée dans la table `config`. Le user `jeedom_mcp_ro` récupère la valeur opaque ; PHP décrypte en runtime via `jeedom::getApiKey()`. Test `eqLogic::all` skipé avec message explicite.

### Déploiement daemon

- Fichiers déployés : `_core/db.py`, `_core/auth.py`, `_core/api.py`, `_core/logs.py`, `holmesMcpd.py`, PHP class
- Daemon redémarré avec `--jeedom-apikey` (manquant en prod J0-2) — UP et authentifié
- Réponse 401 JSON confirmée sur token invalide

## Tests unitaires

74/74 passés (+ 2 tests ajoutés : socket override, bug LIKE params). Ruff propre.

## Prochain jalon : J2

- `_domain/sanitize.py` complet (3 mécanismes : whitelist + regex + hard-code)
- Tests unitaires sanitiseur
- Début des 25 tools (`tools/` et `resources/`)
