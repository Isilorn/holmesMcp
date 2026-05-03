# ADR-0020 — jeedom-mcp : projet séparé, plugin Jeedom natif

- **Date** : 2026-05-01
- **Statut** : Accepté
- **Contexte de décision** : session de réflexion stratégique post-release v1.0.1 + échange d'idéation avec Claude Opus 4.7

## Contexte

Après la publication de `jeedom-audit` v1.0.0, une question de fond a émergé sur le forum Jeedom : la skill Claude Code et le protocole MCP sont-ils complémentaires ou en concurrence ? La réponse a conduit à reconsidérer la roadmap V2/V3 initialement planifiée (ADR-0006, PLANNING §10).

Deux constats issus de l'échange d'idéation :

1. **Les personas sont différents** : les utilisateurs de Claude Code acceptent un setup technique (SSH, Python, ~/.my.cnf). Les utilisateurs de Claude Desktop ou Cursor veulent une URL et zéro setup.

2. **Les architectures servent des usages différents** : une skill Claude Code est orientée "méthode" (orchestration adaptative, diagnostic forensique, connaissance domaine dans SKILL.md). Un serveur MCP est orienté "outil" (interface fixe, déterministe, consommable par n'importe quel client LLM).

Les capacités modifiantes prévues en V2/V3 (lancer scénario, activer/désactiver, écrire variable dataStore) correspondent au paradigme MCP — elles sont inutilement contraintes dans une skill Claude Code.

## Décision

**Créer un projet séparé `jeedom-mcp`** : un plugin Jeedom natif qui expose les données et commandes de la box via le protocole MCP (Model Context Protocol, Anthropic).

Ce projet est **distinct de `jeedom-skills`** — autre repo, autre cycle de release, autre distribution.

### Ce que jeedom-mcp contiendra

| Catégorie | Exemples |
|---|---|
| Outils lecture | Équipements, scénarios, commandes, plugins, logs, historique |
| Outils écriture | Lancer scénario, activer/désactiver, exécuter commande action, écrire variable dataStore |
| Outils config légère | Renommages, activation Types Génériques (V2+ de jeedom-mcp) |

### Architecture cible

**Option C (ADR-0019) : plugin Jeedom natif**

```
[Claude Desktop / Cursor / n'importe quel client MCP]
        ↓ HTTP/SSE
[Plugin jeedom-mcp — box Jeedom]
        ↓ PHP/MySQL natif Jeedom
[MySQL + logs + API Jeedom]
```

- Installation via le market Jeedom (UX familière aux Jeedomistes)
- Démarrage/arrêt géré par Jeedom
- Pas de dépendance Python sur la box
- Configuration via l'UI Jeedom
- Authentification par clé API Jeedom existante

### Ce que jeedom-mcp n'est pas

- **Pas une évolution de jeedom-audit** : les deux projets coexistent, servent des personas différents
- **Pas un remplacement de la skill** : `jeedom-audit` garde sa valeur propre (orchestration adaptative, forensique causale, connaissance domaine dans SKILL.md)
- **Pas dans ce repo** : `jeedom-skills` reste lecture seule absolue (voir amendement ADR-0006)

## Options écartées

### Option A — MCP server local (Option A de ADR-0019)

`mcp_server.py` sur la machine cliente qui wrappe les scripts existants. Écarté : même persona que la skill (power users avec SSH + Python), pas de gain réel. Crée de la dette sans ouvrir de nouveau marché.

### Extension de jeedom-audit V2

Ajouter des capacités modifiantes à la skill existante. Écarté : détruirait la proposition de valeur "lecture seule absolue" qui est devenue identitaire. Mélange deux paradigmes (méthode vs outil) dans un seul produit.

## Conséquences

- ✅ `jeedom-audit` reste lecture seule absolue à perpétuité (ADR-0006 amendé)
- ✅ `jeedom-mcp` adresse les Jeedomistes sur Claude Desktop / Cursor — persona distinct
- ✅ Pas de conflit avec les plugins MCP existants (MCP AI Server, MP_Server) : la différence est l'accès MySQL direct + distribution open source + gratuit
- ⚠️ Effort de développement significatif : plugin PHP + daemon MCP — hors périmètre de ce repo
- ⚠️ La session d'idéation formelle (avec modèle de raisonnement approfondi) est prévue pour définir l'architecture détaillée avant de commencer l'implémentation
- 🔗 ADR-0019 (superseded), ADR-0006 (amendement lecture seule perpétuelle)
