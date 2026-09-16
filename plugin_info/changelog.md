# Changelog Holmes MCP

## v1.2.2 — 2026-09-16

Correction de fond sur la recherche d'usages, et trois corrections de confidentialité.

**Les scénarios imbriqués étaient invisibles.** Un scénario Jeedom est un arbre de blocs, mais
seuls les blocs de premier niveau sont rattachés au scénario dans la base : les blocs imbriqués
s'atteignent de parent en parent. Les outils s'arrêtaient au premier niveau.

- `find_command_usages` et `find_equipment_usages` ne trouvaient que les usages portés par un bloc
  de premier niveau — **69 % des blocs sont imbriqués** sur une installation de référence, et
  87 commandes sur 165 étaient déclarées « inutilisées » alors qu'elles servaient dans un scénario.
- `find_scenario_dependencies` souffrait en plus de l'inverse : il **inventait** des rattachements
  (un bloc `1` était reconnu dans un bloc `100`), rendant 21 réponses fausses sur 63 scénarios.
- La remontée est désormais **récursive** et le rattachement reste une comparaison exacte : sur
  l'installation de référence, les 289 liens réels sont retrouvés, sans aucune invention.

**Confidentialité**

- La table de configuration rendait ses valeurs **en clair** lorsque la requête ne demandait pas
  la colonne `key` : c'est elle qui permet de juger si une valeur est sensible. `query_sql` ajoute
  désormais cette colonne à votre requête et vous le dit ; quand il ne peut pas le faire sans
  changer le sens de la requête (`DISTINCT`, agrégat), les valeurs sont masquées et la réponse
  explique pourquoi. Pour explorer la configuration, `get_config` reste le chemin direct — il n'a
  jamais été concerné.
- Le filtrage par table ne s'appliquait pas aux tables dont le nom porte des majuscules
  (`eqLogic`, `dataStore`, `historyArch`) lorsqu'elles étaient interrogées par `query_sql`.
- Les agrégats sont maintenant lisibles : `SELECT COUNT(*) FROM scenario` rendait `***FILTERED***`
  au lieu du compte. Un alias simple (`SELECT une_colonne AS n`) ne contourne pas le filtrage.

**Transparence**

- `query_sql` déclare `limit_applied` et `truncated` : une troncature n'est plus à deviner.

**Qualité** : 820 tests unitaires, 100 % de couverture sur le module de sanitisation, 199 tests
d'intégration sur box réelle (Jeedom 4.6.1). Détail : `docs/decisions/ADR-0023.md`.

## v1.2.1 — 2026-09-16

Correctif de confidentialité sur la sanitisation, et validation sur Jeedom 4.6.

**Sécurité — cinq valeurs sensibles pouvaient être transmises en clair à un client MCP.**

- Le filtre reconnaissait `apikey`, `api_key`, `access_key` et `private_key`, mais **pas le mot
  `key` seul** : une clé de configuration nommée `keyGMG` ou `jawglabKey` passait donc en clair.
  Les identifiants sont désormais **découpés en mots** (frontières camelCase, `_`, `::`, `-`, `.`)
  et chaque mot est confronté au filtre. `api` est masqué en correspondance exacte — `apiUrl` et
  `apiVersion` restent visibles, ce ne sont pas des secrets.
- Les extras par plugin n'étaient **pas appliqués à la table de configuration**, là où vivent les
  identifiants de compte : le plugin est maintenant lu depuis la ligne elle-même, aucun appelant ne
  peut l'omettre. Extras ajoutés pour les logins de `cozytouch`, `geotrav`, `mail`, `openvpn`,
  `SomfyUnified`.
- Les **identifiants techniques restent visibles** — `appId`, `client_id`, `installed_app_id`,
  `installUUID` : ce sont des références, pas des secrets, et les masquer nuirait au diagnostic.

**Compatibilité**

- Validé sur **Jeedom 4.6.1** (Debian 12 Bookworm x86_64) : 187 tests d'intégration sur box réelle,
  27/27 outils au test de fumée, aucune régression depuis 4.5.3. La version minimale requise reste
  **4.5**.

**Qualité** : 763 tests unitaires, 100 % de couverture sur le module de sanitisation.


## v1.2.0 — 2026-05-06

Nouveaux outils d'audit et de refactoring (J8-2) — couverture complète des workflows jeedom-audit.

- Nouvel outil `find_equipment_usages(equipment_id)` : retourne les scénarios qui utilisent un équipement via ses commandes (27e tool)
- `get_health_summary` : deux nouvelles métriques — commandes mortes (équipement désactivé ou supprimé) et commandes info historisées sans aucune donnée
- `list_datastore_variables(orphaned=True)` : filtre les variables non référencées dans aucune expression de scénario
- `find_commands_advanced(generic_type_missing=True)` : commandes info sans Type Générique — utile pour l'audit de couverture
- `find_equipments_advanced(has_warning=True)` : équipements en état warning ou danger
- `find_scenarios_advanced(called_while_inactive=True)` : scénarios désactivés mais appelés dans les actions d'un autre scénario

## v1.1.1 — 2026-05-05

Correction de bug — compatibilité MariaDB (J7bis-2).

- Correction : `find_command_usages` échouait sur MariaDB (Jeedom Bookworm) lors de la recherche dans les expressions de scénarios — syntaxe `CAST AS JSON` remplacée par `JSON_SEARCH`

## v1.1.0 — 2026-05-05

Améliorations pré-bêta (J7bis-1) — qualité query_sql et nouvel outil d'analyse de dépendances.

- Nouvel outil `find_command_usages(cmd_id)` : retourne les scénarios déclenchés par une commande, les scénarios qui l'utilisent en condition/action, et les variables dataStore qui la référencent
- `query_sql` : auto-backtick des mots réservés MySQL `trigger`, `repeat`, `update` dans les requêtes utilisateur (plus besoin de les écrire manuellement)
- Documentation : comportement LIMIT de `query_sql` explicité dans le diagnostic MkDocs (LIMIT 50 auto-injecté, max 200)
- FAQ : précision plateforme cible — Jeedom 4.5+ sur Debian 12 Bookworm x86_64

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
