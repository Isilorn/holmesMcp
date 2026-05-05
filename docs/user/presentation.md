# Présentation

## Qu'est-ce que Holmes MCP ?

Holmes MCP est un **plugin Jeedom natif** qui expose votre box domotique comme serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io). Il permet à un assistant IA (Claude, Cursor…) de lire et analyser votre installation Jeedom en langage naturel.

Le nom "Holmes" est un clin d'œil à Sherlock Holmes : il observe, déduit et raconte — mais ne touche jamais à la scène.

## Architecture

```
Claude Desktop / Claude Code / Cursor
        │  HTTP + Bearer token
        ▼
  ┌─────────────────┐
  │  Daemon Python  │  FastMCP (spec MCP 2025-03-26, Streamable HTTP)
  │  port 8765      │  25 tools + 5 resources
  └────┬──────┬─────┘
       │      │
  MySQL RO   API JSON-RPC   Fichiers logs
  jeedom_mcp_ro  localhost     /var/log/jeedom/
```

**Trois canaux d'accès à la box, tous en lecture seule :**

| Canal | Usage |
| --- | --- |
| MySQL `jeedom_mcp_ro` | Équipements, scénarios, configuration, historiques |
| API JSON-RPC localhost | État temps réel (currentValue, lastLaunch, state scénario) |
| Fichiers logs | Lecture directe des logs Jeedom (`/var/log/jeedom/`) |

**Deux composants :**

- **Daemon Python** — le cœur du plugin : serveur MCP FastMCP, authentification Bearer, sanitisation, tools et resources
- **Plugin PHP** — enveloppe Jeedom market : manifeste, UI de configuration, démarrage/arrêt daemon, génération de tokens

## Cas d'usage

### Audit d'installation

> *"Quels équipements sont désactivés ? Quels plugins n'ont aucun équipement actif ?"*

Holmes MCP lit l'intégralité de votre configuration Jeedom et répond en langage naturel.

### Diagnostic de scénario

> *"Pourquoi mon scénario 'Réveil' ne se déclenche pas le vendredi ?"*

Le LLM lit la structure du scénario, ses déclencheurs, son dernier log d'exécution et diagnostique.

### Exploration

> *"Quelles commandes du salon sont historisées ? Quel équipement pilote la VMC ?"*

25 tools de recherche et de navigation couvrent l'ensemble de votre installation.

### Diagnostic système

> *"Y a-t-il des daemons en erreur ? Des messages critiques récents ?"*

`get_health_summary` interroge les plugins KO, les messages système et les crons actifs.

## Ce que Holmes MCP ne fait pas (V1)

Holmes MCP est **strictement en lecture seule** en V1. Il ne peut pas :

- Allumer ou éteindre un équipement
- Déclencher ou arrêter un scénario
- Modifier une configuration Jeedom
- Écrire dans la base de données

Ces fonctionnalités sont candidates pour V2, via l'API JSON-RPC (jamais via SQL direct).

## Compatibilité

| Composant | Version minimale |
| --- | --- |
| Jeedom | 4.5 |
| Debian | 12 (Bookworm) |
| Python | 3.11 |
| Spec MCP | 2025-03-26 (Streamable HTTP) |

**Clients MCP compatibles :** Claude Desktop, Claude Code, Cursor, MCP Inspector, et tout client supportant la spec MCP 2025-03-26 en HTTP.
