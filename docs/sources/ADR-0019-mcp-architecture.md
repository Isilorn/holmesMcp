---
id: ADR-0019
titre: Architecture MCP — intégration d'un serveur MCP dans jeedom-audit
statut: Superseded by ADR-0020
date: 2026-04-30
---

# ADR-0019 — Architecture MCP

## Statut

**En réflexion** — pas de décision prise. Ce document capture les options et les questions ouvertes pour une session d'idéation.

---

## Contexte et motivations

La skill `jeedom-audit` fonctionne aujourd'hui comme une couche "méthode" : SKILL.md contient le domaine knowledge, les scripts Python sont appelés via Bash par Claude Code, et l'orchestration adaptative est assurée par Claude lui-même.

Cette architecture a une limite : elle est couplée à Claude Code. Claude Desktop, Cursor, n8n et les autres clients MCP ne peuvent pas l'utiliser.

Le protocole MCP (Model Context Protocol, Anthropic) permet d'exposer des outils à n'importe quel client compatible. Les scripts Python de jeedom-audit (`db_query.py`, `logs_query.py`, `scenario_tree_walker.py`, `usage_graph.py`, `api_call.py`, `resolve_cmd_refs.py`, `version_check.py`) sont de bons candidats à cette migration — ils sont déjà déterministes et bien factorisés.

### Ligne de partage skill / MCP

| Couche | Ce qu'elle contient | Doit bouger en MCP ? |
|---|---|---|
| Scripts Python | Outils déterministes (entrée fixe → sortie prévisible) | ✅ Oui |
| `SKILL.md` | Domaine knowledge, gotchas, méthodes d'orchestration | ❌ Non |
| Orchestration adaptative | Décider quels outils appeler selon les résultats | ❌ Non |
| Templates de rapport | Formats de sortie WF1-WF13 | ❌ Non |

---

## Options d'implémentation

### Option A — MCP server local (machine cliente)

Le serveur MCP tourne sur le Mac/PC de l'utilisateur. Il se connecte à Jeedom via SSH, exactement comme la skill actuelle.

```
[Claude Desktop / Claude Code]
        ↓ MCP (stdio)
[mcp_server.py — localhost]
        ↓ SSH
[Box Jeedom — MySQL + logs + API]
```

**Avantages :**
- Même infrastructure que la skill actuelle (alias SSH, `~/.my.cnf`, `credentials.json`)
- Pas de port à ouvrir sur la box
- Python 3.10+ garanti côté client (déjà requis par la skill)
- Migration naturelle : `mcp_server.py` (~100 lignes) wrappe les scripts existants

**Inconvénients :**
- Le process MCP doit être actif quand on utilise Claude Desktop
- Toujours couplé à la machine du client

**Configuration :**
```json
// ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "jeedom-audit": {
      "command": "python3",
      "args": ["~/.claude/skills/jeedom-audit/mcp_server.py"]
    }
  }
}
```

---

### Option B — MCP server sur la box Jeedom

Le serveur MCP tourne directement sur la box. Il accède à MySQL et aux logs en local, sans SSH.

```
[Claude Desktop / Claude Code]
        ↓ HTTP/SSE (réseau local ou VPN)
[mcp_server.py — box Jeedom :8765]
        ↓ localhost
[MySQL + logs + API Jeedom]
```

**Avantages :**
- MySQL en accès direct (plus rapide, pas de tunnel SSH)
- Côté client : juste une URL, aucune dépendance Python locale
- Logs et fichiers accessibles directement

**Inconvénients :**
- Python 3.10+ requis sur la box (souvent absent sur Raspberry Pi / Debian standard)
- Process management à prévoir (systemd ou plugin Jeedom)
- Sécurité réseau à gérer (authentification, HTTPS si exposé hors LAN)
- Ressources permanentes sur une box potentiellement légère
- Mises à jour du serveur MCP à gérer côté box

**Questions ouvertes :**
- Quel mécanisme de démarrage ? (systemd unit, plugin Jeedom, script init)
- Comment authentifier les appels MCP ? (token statique, clé API Jeedom)
- HTTP/SSE ou stdio via SSH tunnel ?

---

### Option C — Plugin Jeedom natif

Le serveur MCP est packagé comme un plugin Jeedom officiel. Il s'installe depuis le market, se configure via l'UI Jeedom, et expose les outils MCP.

```
[Claude Desktop / Claude Code]
        ↓ HTTP/SSE
[Plugin jeedom-audit-mcp — box Jeedom]
        ↓ PHP/MySQL natif Jeedom
[MySQL + logs + API Jeedom]
```

**Avantages :**
- Installation via le market Jeedom (UX familière)
- Démarrage/arrêt géré par Jeedom comme n'importe quel daemon
- Configuration via l'UI
- Pas de dépendance Python (implémentation PHP possible)

**Inconvénients :**
- Effort de développement significatif (plugin PHP + daemon Python ou PHP)
- Maintenance d'un plugin Jeedom (market, versions, compatibilité)
- Hors du périmètre "skill Claude Code" initial
- Risque de recoupement avec MCP AI Server / MP_Server existants

---

## Questions transversales

1. **Skill + MCP ou MCP seul ?** La skill garde-t-elle sa raison d'être si les scripts deviennent des outils MCP ? L'orchestration adaptative (forensique causale, audit général) justifie-t-elle de maintenir les deux ?

2. **Consommation de tokens** : SKILL.md en contexte a un coût non négligeable. Des outils MCP bien définis permettraient-ils de le réduire en n'incluant que les instructions nécessaires selon le workflow ?

3. **Audience cible** : les utilisateurs Claude Code acceptent un setup technique (alias SSH, Python). Les utilisateurs Claude Desktop ou Cursor veulent une URL. Ce sont deux personas différents — faut-il les servir tous les deux ?

4. **Relation avec les plugins existants** (MCP AI Server, MP_Server) : un MCP jeedom-audit sur la box serait en concurrence directe. La différence (accès MySQL direct vs API seule) est-elle suffisante pour justifier une coexistence ?

5. **Modèle de distribution** : la skill est un zip déposé dans `~/.claude/skills/`. Un MCP server local suit le même modèle. Un MCP sur la box nécessite un mécanisme différent. Faut-il unifier ou accepter deux modes d'installation ?

---

## Pistes à explorer en idéation

- Architecture hybride : MCP server local qui wrappe les scripts existants + SKILL.md réduit qui l'utilise
- MCP server minimal (Option A) comme V2.0, Option B comme V2.1 si demande communauté
- Séparer le "MCP des outils" (Option A, rapide) du "MCP sur la box" (Option B/C, effort)
- Évaluer si la skill peut consommer ses propres outils MCP pour réduire les tokens

---

## Décision

**Aucune décision prise à ce stade.** Ce document est la base d'une session d'idéation avec un modèle de raisonnement approfondi.
