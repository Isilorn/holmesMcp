# Sphere jeedom-audit

## Qu'est-ce que jeedom-audit ?

[jeedom-audit](https://github.com/Isilorn/jeedom-audit) est une skill Claude Code — un ensemble de workflows d'audit de box Jeedom, utilisable directement dans Claude Code via la commande `/jeedom-audit`.

Holmes MCP et jeedom-audit sont deux outils complémentaires du même écosystème, développés par le même auteur.

## Différence entre jeedom-audit et Holmes MCP

| | jeedom-audit | Holmes MCP |
| --- | --- | --- |
| **Type** | Skill Claude Code (workflows) | Plugin Jeedom (serveur MCP) |
| **Accès box** | SSH direct (via Claude Code) | HTTP MCP (Bearer token) |
| **Clients** | Claude Code uniquement | Claude Desktop, Cursor, Claude Code… |
| **Usage** | Audit structuré par workflow | Exploration libre en langage naturel |
| **Installation** | Aucune installation sur la box | Plugin installé sur la box |

## Holmes MCP remplace jeedom-audit ?

**Non — ils sont complémentaires.**

- **jeedom-audit** est adapté aux audits structurés et répétables depuis Claude Code, avec des workflows précis par domaine (scénarios, équipements, plugins…)
- **Holmes MCP** permet une exploration en langage naturel depuis n'importe quel client MCP, sans SSH

Holmes MCP a été conçu pour couvrir les **13 workflows de jeedom-audit** — la matrice de couverture a été vérifiée en J1 du projet (ADR-0019).

## Matrice de couverture

Les 13 workflows jeedom-audit sont couverts par Holmes MCP :

| Workflow jeedom-audit | Tools Holmes MCP couvrant |
| --- | --- |
| Audit équipements | `list_equipments`, `find_equipments_advanced`, `get_equipment` |
| Audit commandes | `list_commands`, `find_commands_advanced`, `get_command_history` |
| Audit scénarios | `list_scenarios`, `find_scenarios_advanced`, `describe_scenario` |
| Dépendances scénarios | `find_scenario_dependencies`, `get_scenario_structure` |
| Audit plugins | `list_plugins`, `get_health_summary` |
| Audit objets/pièces | `list_objects` |
| Audit variables | `list_datastore_variables`, `get_datastore_variable` |
| Vue d'ensemble | `get_install_overview` |
| Configuration | `get_config` |
| Logs & diagnostic | `list_log_files`, `tail_log`, `get_health_summary` |
| Recherche transverse | `search_text` |
| SQL libre | `query_sql` |
| Résolution références | `describe_scenario` (résout automatiquement `#[O][E][C]#`) |

## Migration depuis jeedom-audit

Si vous utilisez jeedom-audit depuis Claude Code et souhaitez passer à Holmes MCP :

1. Installez Holmes MCP sur votre box ([Installation](installation.md))
2. Configurez le plugin dans `.mcp.json` de Claude Code ([Clients MCP](clients-mcp.md))
3. Vous pouvez continuer à utiliser les workflows jeedom-audit **en parallèle** — les deux coexistent sans conflit

Holmes MCP ne remplace pas jeedom-audit pour les workflows avancés nécessitant SSH (écriture de fichiers, modifications système, opérations interactives).
