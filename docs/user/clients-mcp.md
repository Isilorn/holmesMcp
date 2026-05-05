# Clients MCP

Holmes MCP expose un serveur HTTP compatible avec la spec MCP 2025-03-26 (Streamable HTTP). Les exemples ci-dessous utilisent des placeholders — remplacez-les par vos vraies valeurs.

| Placeholder | Exemple |
| --- | --- |
| `<ip-box>` | `203.0.113.10` |
| `<port>` | `8765` |
| `<votre-token>` | Token généré dans la page du plugin |

---

## Claude Code

Claude Code supporte HTTP natif — c'est le client le plus simple à configurer.

Ajoutez Holmes MCP à votre fichier `.mcp.json` (à la racine du projet ou dans `~/.claude/`):

```json
{
  "mcpServers": {
    "holmes": {
      "type": "http",
      "url": "http://<ip-box>:<port>/mcp",
      "headers": {
        "Authorization": "Bearer <votre-token>"
      }
    }
  }
}
```

Redémarrez Claude Code ou rechargez la configuration. Holmes MCP apparaît dans la liste des serveurs MCP disponibles.

!!! tip "Vérification rapide"
    Dans Claude Code, tapez `/mcp` pour voir les serveurs connectés et leur statut.

---

## Claude Desktop

Claude Desktop ne supporte pas HTTP direct. Utilisez `mcp-remote` comme pont stdio→HTTP.

### Installer mcp-remote

```bash
npm install -g mcp-remote
```

### Configurer claude_desktop_config.json

Sur **macOS** : `~/Library/Application Support/Claude/claude_desktop_config.json`
Sur **Windows** : `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "holmes": {
      "command": "mcp-remote",
      "args": [
        "http://<ip-box>:<port>/mcp",
        "--header",
        "Authorization: Bearer <votre-token>"
      ]
    }
  }
}
```

Redémarrez Claude Desktop. Holmes MCP doit apparaître dans les outils disponibles (icône marteau dans l'interface).

!!! warning "mcp-remote et Node.js"
    `mcp-remote` requiert Node.js 18+. Vérifiez avec `node --version`. Sous Windows, l'installation de Node.js via [nodejs.org](https://nodejs.org) est recommandée.

---

## Cursor

La configuration Cursor est similaire à Claude Desktop — Cursor utilise aussi `mcp-remote`.

Ouvrez les paramètres Cursor → **MCP** → **Add new MCP server** :

```json
{
  "holmes": {
    "command": "mcp-remote",
    "args": [
      "http://<ip-box>:<port>/mcp",
      "--header",
      "Authorization: Bearer <votre-token>"
    ]
  }
}
```

---

## MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) est un outil de débogage web pour les serveurs MCP. Utile pour tester et explorer Holmes MCP sans configurer un client LLM.

```bash
npx @modelcontextprotocol/inspector http://<ip-box>:<port>/mcp
```

Dans l'interface Inspector, ajoutez le header d'authentification :

```http
Authorization: Bearer <votre-token>
```

Vous pouvez ensuite parcourir les 25 tools, lire les 5 resources et exécuter des appels manuellement.

---

## Dépannage connexion

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `Connection refused` | Daemon arrêté ou mauvais port | Vérifier statut daemon + port dans la config |
| `401 Unauthorized` | Token invalide ou absent | Vérifier le header `Authorization: Bearer <token>` |
| `Timeout` | Box inaccessible depuis le client | Vérifier que client et box sont sur le même réseau LAN |
| Tools vides dans Claude Desktop | `mcp-remote` non installé | `npm install -g mcp-remote` |
