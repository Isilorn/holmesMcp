# Holmes MCP

> *Holmes observe, déduit, raconte. Il ne touche jamais à la scène de crime, sans jamais exposer les secrets de votre maison.*

**Holmes MCP** est un plugin Jeedom natif open source qui expose votre box Jeedom comme serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) en **lecture seule**.

Compatible avec **Claude Desktop**, **Claude Code**, **Cursor** et tout client MCP.

---

## À quoi ça sert ?

Holmes MCP permet à un assistant IA (Claude, Cursor…) de **lire et analyser votre installation Jeedom** sans jamais modifier quoi que ce soit :

- Audit complet de votre installation (équipements, scénarios, plugins)
- Diagnostic en langage naturel ("pourquoi ce scénario ne se déclenche pas ?")
- Assistance à la conception ("quels équipements pilotent le salon ?")
- Exploration des logs et de la santé système

## Ce que Holmes MCP n'est pas (V1)

Holmes MCP est **lecture seule**. Il ne peut pas allumer une lumière, déclencher un scénario, ni modifier un paramètre. Ces fonctions sont prévues pour V2.

---

## Démarrage rapide

1. Installez le plugin depuis le **market Jeedom** → [Guide d'installation](installation.md)
2. Installez les **dépendances Python** (bouton "Dépendances" dans la page plugin)
3. **Démarrez le daemon** depuis la page de configuration
4. **Générez un token** Bearer pour votre utilisateur Jeedom
5. Collez l'**URL MCP + Bearer token** dans votre client → [Clients MCP](clients-mcp.md)

---

## Navigation

| Section | Contenu |
| --- | --- |
| [Présentation](presentation.md) | Architecture, cas d'usage, limites V1 |
| [Installation](installation.md) | Prérequis, install depuis le market, user MySQL RO |
| [Configuration](configuration.md) | Token, port, options daemon |
| [Clients MCP](clients-mcp.md) | Claude Desktop, Claude Code, Cursor, MCP Inspector |
| [Sécurité](securite.md) | Auth Bearer, sanitisation, lecture seule |
| [Tools (25)](tools.md) | Liste complète des 25 tools par famille |
| [Resources (5)](resources.md) | 5 resources URI `jeedom://` |
| [Diagnostic & logs](diagnostic.md) | Logs plugin, vue activité MCP, dépannage |
| [FAQ](faq.md) | Questions fréquentes |
| [Sphere jeedom-audit](jeedom-audit.md) | Lien avec la skill jeedom-audit |
| [Contribuer](contribuer.md) | AGPL-3.0, issues, tests, ADRs |
