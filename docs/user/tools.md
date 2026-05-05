# Tools (25)

Holmes MCP expose **25 tools** répartis en **7 familles**. Tous sont en **lecture seule**.

## Vue d'ensemble

| Famille | Nb | Tools |
| --- | --- | --- |
| [Découverte](#famille-1-decouverte) | 4 | `get_install_overview`, `list_objects`, `list_plugins`, `get_config` |
| [Équipements & Commandes](#famille-2-equipements-et-commandes) | 7 | `list_equipments`, `find_equipments_advanced`, `get_equipment`, `find_equipment_by_name`, `list_commands`, `find_commands_advanced`, `get_command_history` |
| [Scénarios](#famille-3-scenarios) | 7 | `list_scenarios`, `find_scenarios_advanced`, `get_scenario`, `get_scenario_structure`, `describe_scenario`, `find_scenario_dependencies`, `get_scenario_log` |
| [Variables DataStore](#famille-4-variables-datastore) | 2 | `list_datastore_variables`, `get_datastore_variable` |
| [Logs & Diagnostic](#famille-5-logs-et-diagnostic) | 3 | `list_log_files`, `tail_log`, `get_health_summary` |
| [Recherche transverse](#famille-6-recherche-transverse) | 1 | `search_text` |
| [SQL libre](#famille-7-sql-libre) | 1 | `query_sql` |

---

## Famille 1 — Découverte

### `get_install_overview`

Snapshot général de l'installation Jeedom : version, comptages globaux (équipements, commandes, scénarios, plugins, objets).

Aucun paramètre.

**Exemple d'usage :** *"Combien d'équipements actifs ai-je ?"*

---

### `list_objects`

Hiérarchie complète des objets/pièces Jeedom avec leurs relations parent/enfant.

Aucun paramètre. Limite : 500 objets.

**Exemple d'usage :** *"Quelle est l'arborescence de mes pièces ?"*

---

### `list_plugins`

Liste des plugins installés avec leur statut (actif/inactif) et leur catégorie.

Aucun paramètre. Limite : 200 plugins.

**Exemple d'usage :** *"Quels plugins sont installés et actifs ?"*

---

### `get_config`

Configuration Jeedom par namespace de plugin.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `plugin` | `string` | `null` | Namespace du plugin (ex. `jMQTT`). `null` ou `*` pour tous |
| `key_pattern` | `string` | `null` | Filtre LIKE sur la clé (ex. `%mqtt%`) |

Limite : 200 entrées. Les valeurs sensibles sont sanitisées.

**Exemple d'usage :** *"Quelle est la configuration du plugin Z-Wave ?"*

---

## Famille 2 — Équipements et Commandes

### `list_equipments`

Liste paginée des équipements avec filtres.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `object_id` | `int` | `null` | Filtrer par objet/pièce |
| `plugin` | `string` | `null` | Filtrer par plugin |
| `is_enable` | `bool` | `null` | `true` = actifs uniquement |
| `limit` | `int` | `100` | Max résultats |
| `offset` | `int` | `0` | Décalage pagination |

---

### `find_equipments_advanced`

Recherche avancée multi-critères sur les équipements.

| Paramètre | Type | Description |
| --- | --- | --- |
| `name_contains` | `string` | Filtre sur le nom (insensible à la casse) |
| `object_id` | `int` | Filtrer par objet |
| `plugin` | `string` | Filtrer par plugin |
| `is_enable` | `bool` | Actifs uniquement |
| `generic_type` | `string` | Type générique Jeedom (ex. `LIGHT_STATE`) |
| `tags` | `string` | Tags de l'équipement |
| `limit` | `int` | Max 50 résultats |

---

### `get_equipment`

Détail complet d'un équipement : configuration, commandes, état temps réel.

| Paramètre | Type | Description |
| --- | --- | --- |
| `equipment_id` | `int` | **Requis.** Identifiant numérique de l'équipement |

Les champs sensibles de la configuration sont automatiquement sanitisés.

**Exemple d'usage :** *"Montre-moi tous les détails de l'équipement #42."*

---

### `find_equipment_by_name`

Recherche floue d'un équipement par son nom.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `name` | `string` | — | **Requis.** Nom ou fragment de nom |
| `limit` | `int` | `10` | Max résultats |

**Exemple d'usage :** *"Trouve l'équipement qui s'appelle 'thermomètre salon'."*

---

### `list_commands`

Liste des commandes d'un équipement avec leur état temps réel optionnel.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `equipment_id` | `int` | — | **Requis.** ID équipement |
| `cmd_type` | `string` | `null` | `info` ou `action` |
| `limit` | `int` | `200` | Max résultats |
| `offset` | `int` | `0` | Pagination |

---

### `find_commands_advanced`

Recherche avancée multi-critères sur les commandes.

| Paramètre | Type | Description |
| --- | --- | --- |
| `name_contains` | `string` | Filtre sur le nom |
| `equipment_id` | `int` | Restreindre à un équipement |
| `cmd_type` | `string` | `info` ou `action` |
| `subtype` | `string` | Sous-type (`binary`, `numeric`, `string`…) |
| `generic_type` | `string` | Type générique Jeedom |
| `is_historized` | `bool` | Commandes historisées uniquement |
| `limit` | `int` | Max 50 |

---

### `get_command_history`

Historique des valeurs d'une commande de type `info`.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `cmd_id` | `int` | — | **Requis.** ID de la commande |
| `limit` | `int` | `100` | Nombre de points d'historique |

**Exemple d'usage :** *"Quelle est l'évolution de la température du salon ces dernières heures ?"*

---

## Famille 3 — Scénarios

### `list_scenarios`

Liste paginée des scénarios avec leur état temps réel (actif/inactif, dernier lancement).

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `group` | `string` | `null` | Filtrer par groupe |
| `is_active` | `bool` | `null` | Actifs uniquement |
| `limit` | `int` | `100` | Max résultats |
| `offset` | `int` | `0` | Pagination |

---

### `find_scenarios_advanced`

Recherche avancée multi-critères sur les scénarios.

| Paramètre | Type | Description |
| --- | --- | --- |
| `name_contains` | `string` | Filtre sur le nom |
| `group` | `string` | Filtrer par groupe |
| `is_active` | `bool` | Actifs uniquement |
| `mode` | `string` | Mode déclenchement (`schedule`, `provoke`, `all`) |
| `trigger_type` | `string` | Type de déclencheur |
| `limit` | `int` | Max 50 |

---

### `get_scenario`

Détail complet d'un scénario : configuration, déclencheurs, état temps réel.

| Paramètre | Type | Description |
| --- | --- | --- |
| `scenario_id` | `int` | **Requis.** ID du scénario |

---

### `get_scenario_structure`

Arbre structurel brut d'un scénario (blocs, conditions, actions imbriquées).

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `scenario_id` | `int` | — | **Requis.** ID du scénario |
| `max_depth` | `int` | `3` | Profondeur maximale de l'arbre |
| `follow_scenario_calls` | `int` | `0` | Suivre les appels à d'autres scénarios (0 = non) |

---

### `describe_scenario`

Description lisible par un LLM du scénario : résumé en langage naturel des blocs et conditions, avec **résolution automatique** des références `#[Objet][Équipement][Commande]#`.

| Paramètre | Type | Description |
| --- | --- | --- |
| `scenario_id` | `int` | **Requis.** ID du scénario |

!!! tip "Tool recommandé pour le diagnostic"
    `describe_scenario` est le tool le plus utile pour analyser un scénario — il produit une description compréhensible par le LLM, avec les vrais noms des équipements et commandes résolus.

**Exemple d'usage :** *"Explique-moi ce que fait le scénario 'Réveil matinal'."*

---

### `find_scenario_dependencies`

Trouve les scénarios qui appellent ce scénario (callers).

| Paramètre | Type | Description |
| --- | --- | --- |
| `scenario_id` | `int` | **Requis.** ID du scénario |

**Exemple d'usage :** *"Quels scénarios déclenchent le scénario #15 ?"*

---

### `get_scenario_log`

Log du dernier run d'un scénario.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `scenario_id` | `int` | — | **Requis.** ID du scénario |
| `lines` | `int` | `100` | Nombre de lignes de log |

---

## Famille 4 — Variables DataStore

### `list_datastore_variables`

Liste des variables du dataStore Jeedom avec filtres.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `var_type` | `string` | `null` | `global` ou `scenario` |
| `link_id` | `int` | `null` | ID du scénario lié (si `var_type=scenario`) |
| `key_pattern` | `string` | `null` | Filtre LIKE sur le nom de variable |
| `limit` | `int` | `100` | Max 200 |
| `offset` | `int` | `0` | Pagination |

---

### `get_datastore_variable`

Valeur d'une variable dataStore spécifique.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `key` | `string` | — | **Requis.** Nom exact de la variable |
| `var_type` | `string` | `null` | Restreindre au type |
| `link_id` | `int` | `null` | Restreindre à un scénario |

---

## Famille 5 — Logs et Diagnostic

### `list_log_files`

Liste tous les fichiers de logs disponibles dans les répertoires Jeedom.

Aucun paramètre.

---

### `tail_log`

Lecture d'un fichier log avec filtre optionnel.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `log_name` | `string` | — | **Requis.** Nom du fichier log (sans chemin) |
| `lines` | `int` | `100` | Nombre de lignes (max 500) |
| `grep` | `string` | `null` | Filtre texte optionnel (insensible à la casse) |

**Exemple d'usage :** *"Montre-moi les erreurs dans le log du plugin jMQTT."*

---

### `get_health_summary`

Résumé de l'état de santé du système : plugins avec daemon KO, messages système récents, crons actifs.

Aucun paramètre.

**Exemple d'usage :** *"Y a-t-il des plugins en erreur en ce moment ?"*

---

## Famille 6 — Recherche transverse

### `search_text`

Recherche d'un texte dans les noms d'équipements, de commandes, de scénarios et dans les expressions de scénarios.

| Paramètre | Type | Défaut | Description |
| --- | --- | --- | --- |
| `text` | `string` | — | **Requis.** Texte à rechercher (min 2 caractères) |
| `limit` | `int` | `20` | Max résultats par catégorie (max 50) |

Retourne 4 catégories : équipements, commandes, scénarios, expressions.

**Exemple d'usage :** *"Trouve tout ce qui fait référence à 'VMC' dans mon installation."*

---

## Famille 7 — SQL libre

### `query_sql`

Exécute une requête SELECT sur la base Jeedom.

| Paramètre | Type | Description |
| --- | --- | --- |
| `sql` | `string` | **Requis.** Requête SQL (SELECT uniquement) |

!!! warning "Sécurité"
    `query_sql` est soumis à des garde-fous stricts : SELECT uniquement, blacklist de tables sensibles (`user`, `session`, `network`…), blacklist de colonnes (`password`, `api`, `token`…), LIMIT automatique plafonné à 200. Voir [Sécurité](securite.md).

**Exemple d'usage :** *"Combien de commandes de type info sont historisées par plugin ?"*
