# Session J6-1 — Vue activité MCP + fix daemon signal handlers

**Date** : 2026-05-05
**Branche** : `develop`
**Commit(s)** : `9776c2b` (vue activité), `d505704` (fix daemon)

---

## Objectif

Implémenter la vue activité MCP dans la page de configuration du plugin (D14.4) :
table des derniers appels outil, filtrée par tool/status, avec auto-refresh.
Corriger le bug de layout Bootstrap détecté sur le formulaire de tokens.

---

## Livrables

| Fichier | Ce qui a changé |
| --- | --- |
| `desktop/php/holmesMcp.php` | Table activité MCP (D14.4), filtre tool/status/date, auto-refresh 30 s ; fix layout tokens (`col-xs-*` + `form-horizontal` + `clearfix`) |
| `resources/holmesMcpd/holmesMcpd.py` | Suppression handlers SIGTERM/SIGINT manuels (overwritten by uvicorn) ; `_remove_pid()` déplacé dans `finally` ; imports `signal`/`sys` supprimés |
| `docs/state/PROJECT_STATE.md` | J6-1 ✅ marquée, prochaine session → J6-2 |

---

## Décisions prises en session

**Bootstrap `col-sm-*` vs `col-xs-*`** : le panel de configuration Jeedom est plus étroit que 768 px — le breakpoint `sm` ne s'active jamais. Solution : `col-xs-*` qui s'applique à toutes les largeurs. Ajout d'un wrapper `<form class="form-horizontal">` pour le clearfix entre les `.form-group` du bloc tokens.

**Handlers SIGTERM/SIGINT retirés** : uvicorn réinstalle ses propres handlers sur la boucle asyncio au démarrage, écrasant silencieusement tout handler installé au niveau module. Le cleanup du PID file dans un bloc `finally` est suffisant et plus robuste — il s'exécute quelle que soit la cause d'arrêt (signal, exception fatale, sortie normale).

**Méthode d'arrêt/démarrage daemon** : décision structurante — uniquement via `holmesMcp::deamon_stop()` / `holmesMcp::deamon_start()` (PHP CLI ou UI Jeedom). `pkill` et `kill` direct sont interdits (ne nettoient pas le PID file, incident SSH storm documenté).

---

## Résultats qualité

| Métrique | Valeur |
| --- | --- |
| Tests unitaires | 664/664 ✅ |
| Couverture globale | 98,38 % |
| Ruff (`holmesMcpd.py`) | propre |

---

## Incidents / anomalies

**Incident MariaDB (2026-05-05, nuit J6-1)** : `innodb_buffer_pool_size = 128 MB` pour une DB de 458 MB → pression constante sur le disque → connexions PHP avortées lors d'écritures → valeurs NULL dans la DB (thermostats, géofencing). Résolu : buffer pool porté à 2 Go, RAM VM Proxmox portée de 4 Go à 8 Go.

**Perte partielle données** : historique présence Géraud + valeurs géofencing Jeedom Connect remises à zéro pendant la session. Causalité non prouvée avec Holmes MCP, corrélation temporelle réelle. Snapshot Proxmox obligatoire avant toute session live (règle élargie).

**SSH storm** : tentatives répétées de `pkill` sans sudo-temp actif → 15+ connexions SSH en 2 minutes (22:26–22:28). Ajout de charge sur une box déjà sous pression. Cause racine : procédure stop/start daemon non documentée → corrigée + mémorisée.

---

## Prochaine sous-session : J6-2

**Objectif** : Enrichissement sanitisation — vérification live des champs exposés pour jMQTT, Alarme, Jeedom Connect, MQTT Manager (ADR-0021).
**Pré-requis** : snapshot Proxmox avant la session (accès SSH avec sudo-temp nécessaire).
