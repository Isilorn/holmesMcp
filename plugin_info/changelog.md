# Changelog Holmes MCP

## v1.0.0 — 2026-05-05

Première version stable — soumission market.

- Documentation utilisateur complète : installation, configuration, clients MCP, sécurité, diagnostic, FAQ
- Icône market officielle (hibou Holmes, 200×200)
- 25 tools de lecture et 5 resources MCP disponibles et validés sur box réelle Jeedom 4.5.3

## v0.6.0 — 2026-05-05

- Vue "Activité MCP" dans l'interface Jeedom : tableau des derniers appels tools (tool appelé, statut, durée), filtre par tool/statut, rafraîchissement automatique toutes les 30 secondes
- Sanitisation renforcée : correction des champs sensibles pour jMQTT (`mqttUser`, `mqttPass`) et 5 noms de plugins corrigés

## v0.5.0 — 2026-05-04

- **25 tools MCP** au total : ajout des familles datastore, logs et SQL restreint
  - `list_datastore_variables`, `get_datastore_variable` : variables globales Jeedom
  - `list_log_files`, `tail_log` : consultation des fichiers de log
  - `get_health_summary` : état de santé global (mises à jour en attente, erreurs, crons)
  - `search_text` : recherche textuelle dans équipements, commandes et scénarios
  - `query_sql` : requêtes SQL SELECT en lecture seule, limité aux tables non sensibles
- **5 resources MCP** : overview, health, scenario, equipment, logs_today — accessibles sans argument depuis n'importe quel client MCP
- Validation complète sur box réelle Jeedom 4.5.3 (smoke test resources/list + resources/read)

## v0.4.1 — 2026-05-04

- Corrections post-audit : champs `position`, `currentValue`, `collectDate` manquants dans la sanitisation
- `get_config` : paramètre `plugin` rendu optionnel, support du wildcard `*`
- `find_scenarios_advanced` : filtre par `mode` ajouté

## v0.4.0 — 2026-05-04

- **18 tools MCP** couvrant l'essentiel de la box :
  - Famille 1 — Découverte : `get_install_overview`, `list_objects`, `list_plugins`, `get_config`
  - Famille 2 — Équipements : `list_equipments`, `find_equipments_advanced`, `get_equipment`, `find_equipment_by_name`, `list_commands`, `find_commands_advanced`, `get_command_history`
  - Famille 3 — Scénarios : `list_scenarios`, `find_scenarios_advanced`, `get_scenario`, `get_scenario_structure`, `describe_scenario`, `find_scenario_dependencies`, `get_scenario_log`
- Enrichissement runtime via l'API Jeedom : état courant des scénarios et valeur courante des commandes
- Validation sur box réelle (68 tests d'intégration, 0 régression)

## v0.3.0 — 2026-05-04

- Sanitisation des données sensibles : 3 mécanismes cumulatifs (liste blanche de champs, expressions régulières, exclusions par plugin)
- Résolution des références `#cmdId#` dans les scénarios → noms lisibles `[Objet][Équipement][Commande]`
- Graphe d'usage : quels scénarios/équipements utilisent une commande donnée

## v0.2.0 — 2026-05-04

- Authentification Bearer par utilisateur Jeedom (token individuel généré depuis la page de configuration)
- Connexion MySQL en lecture seule via un utilisateur dédié `jeedom_mcp_ro`
- Accès aux logs Jeedom et à l'API JSON-RPC localhost
- 18/19 tests d'intégration validés sur box réelle Jeedom 4.5.3

## v0.1.0 — 2026-05-03

- Bootstrap du plugin : structure PHP pour le market Jeedom, daemon Python, CI GitHub Actions

## v0.0.0 — 2026-05-03

- Initialisation du dépôt
