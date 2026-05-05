# Holmes MCP

> *Holmes observe, déduit, raconte. Il ne touche jamais à la scène, sans jamais exposer les secrets de votre maison.*

Plugin Jeedom natif open source qui expose votre box Jeedom comme **serveur MCP** ([Model Context Protocol](https://modelcontextprotocol.io)) en lecture seule.

Orienté audit, diagnostic et assistance à la conception. Pour **Claude Desktop**, **Cursor** et tout client MCP compatible.

---

## Fonctionnalités V1

- **25 tools** de lecture : équipements, commandes, scénarios, plugins, logs, configuration, datastore, SQL restreint
- **5 resources** MCP pour les workflows courants (overview, health, scenario, equipment, logs du jour)
- **Authentification Bearer** par utilisateur Jeedom (token individuel)
- **Sanitisation forte** : 3 mécanismes cumulatifs, aucun credential exposé
- **Vue activité MCP** dans l'interface Jeedom : derniers appels tools, statut, durée
- Installation via le **market Jeedom** — zéro setup côté client

## Prérequis

| Composant | Version minimale |
| --- | --- |
| Jeedom | 4.5+ |
| OS | Debian 12 Bookworm x86_64 |
| Python (auto-installé) | 3.11+ |

## Installation

1. Market Jeedom → rechercher **Holmes MCP**
2. Installer les dépendances (bouton "Dépendances")
3. Démarrer le daemon
4. Configurer un token par utilisateur Jeedom
5. Coller l'URL MCP + Bearer token dans votre client MCP

## Documentation

Documentation complète : **[isilorn.github.io/holmesMcp](https://isilorn.github.io/holmesMcp/)**

## Statut

`v1.0.0` — Version stable V1. 25 tools, 5 resources, authentification Bearer, sanitisation, validé sur Jeedom 4.5.3.

## Licence

[AGPL-3.0](LICENSE) — Holmes MCP est un logiciel libre.
