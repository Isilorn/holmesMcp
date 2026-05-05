# FAQ

## Général

### Holmes MCP peut-il contrôler mes équipements ?

**Non.** Holmes MCP V1 est strictement en **lecture seule**. Il peut lire et décrire votre installation, mais ne peut pas allumer une lumière, déclencher un scénario, ou modifier quoi que ce soit.

Les fonctions d'action (écriture) sont candidates pour V2, via l'API JSON-RPC Jeedom — jamais via SQL direct.

---

### Mes données Jeedom quittent-elles ma box ?

**Les données brutes de la box ne quittent pas votre réseau local.** Holmes MCP fonctionne uniquement en LAN.

Ce qui est envoyé à Anthropic (ou votre provider LLM) : les données retournées par Holmes MCP dans le contexte de votre conversation avec le LLM. Si vous utilisez Claude Desktop avec un compte Anthropic, ces données transitent par les serveurs d'Anthropic selon leur politique de confidentialité.

!!! tip "Si la confidentialité est critique"
    Utilisez Holmes MCP avec un LLM local (Ollama + client MCP compatible) pour que rien ne quitte votre réseau.

---

### Plusieurs utilisateurs peuvent-ils utiliser Holmes MCP simultanément ?

**Oui.** Chaque utilisateur Jeedom dispose de son propre token Bearer. Plusieurs connexions simultanées sont supportées.

---

### Holmes MCP est-il compatible avec Jeedom 4.4 ou antérieur ?

**Non.** Jeedom 4.5 minimum est requis pour la gestion du virtualenv Python (`system::update()`). Jeedom 4.4 et antérieur ne sont pas supportés.

---

### Est-ce compatible avec une installation Jeedom sur Ubuntu ou autre distro ?

Holmes MCP a été développé et testé sur **Debian 12 (Bookworm)**. D'autres distributions pourraient fonctionner mais ne sont pas officiellement supportées. Python 3.11+ est requis.

---

## Sécurité

### Mon token Bearer est-il sécurisé ?

Le token est stocké dans la base Jeedom (chiffré via `User->setOption()`). Il est transmis en HTTP sur votre réseau local. En V1, HTTPS n'est pas supporté — le token est donc visible sur votre réseau LAN si quelqu'un écoute le trafic (attaque man-in-the-middle locale).

**Recommandations :**
- Réservez l'usage à votre réseau local de confiance
- N'exposez pas le port 8765 sur Internet
- Utilisez un VPN pour accéder à distance

---

### Holmes MCP peut-il lire mes mots de passe Jeedom ?

**Non.** La sanitisation (3 mécanismes cumulés) filtre automatiquement les credentials. L'utilisateur MySQL `jeedom_mcp_ro` a uniquement `SELECT` — et même en lisant la table `user`, les colonnes `password` et `api` sont blacklistées dans `query_sql`.

Voir [Sécurité](securite.md) pour le détail complet.

---

### query_sql peut-il modifier la base de données ?

**Non.** `query_sql` n'accepte que des requêtes `SELECT`. Toute autre commande SQL (INSERT, UPDATE, DELETE, DROP…) est rejetée avant exécution. De plus, l'utilisateur MySQL `jeedom_mcp_ro` n'a que `GRANT SELECT` — il serait de toute façon refusé par MySQL.

---

## Installation & Configuration

### Le daemon ne démarre pas après installation, que faire ?

Consultez la section [Diagnostic & logs](diagnostic.md#le-daemon-ne-demarre-pas) pour un guide de dépannage étape par étape.

---

### Je n'ai pas accès à `sudo mysql`. Comment créer l'utilisateur MySQL ?

Si votre user Jeedom MySQL dispose des droits `CREATE USER`, vous pouvez vous connecter directement :

```bash
mysql -u jeedom -p jeedom
```

Sinon, contactez votre hébergeur ou accédez à phpMyAdmin si disponible sur votre installation.

---

### Peut-on changer le port 8765 ?

**Oui.** Dans la page de configuration du plugin, modifiez le port avant de démarrer le daemon. Mettez à jour l'URL dans votre client MCP en conséquence.

---

### Comment savoir quelle version du plugin est installée ?

Dans Jeedom : **Plugins → Gestion des plugins → Holmes MCP**. La version est affichée dans la fiche du plugin. Vous pouvez aussi interroger Holmes MCP via `get_install_overview` qui retourne la version Jeedom (pas directement la version du plugin).

---

## Usage avec les LLM

### Quels clients MCP sont supportés ?

Tout client supportant la spec MCP 2025-03-26 en HTTP. Les clients testés : Claude Code (natif), Claude Desktop (via `mcp-remote`), Cursor (via `mcp-remote`), MCP Inspector.

Voir [Clients MCP](clients-mcp.md).

---

### Holmes MCP fonctionne-t-il avec des LLM autres que Claude ?

**Oui**, si votre client LLM supporte le protocole MCP. Holmes MCP est agnostique au LLM — il expose un serveur MCP standard. Cursor (avec GPT-4 ou autres modèles) fonctionne de la même façon.

---

### Le LLM fait-il des erreurs avec les données Jeedom ?

Le LLM peut mal interpréter des données structurées complexes (scénarios imbriqués, expressions Jeedom). `describe_scenario` est conçu pour produire une description lisible qui réduit ce risque. En cas de doute, vérifiez toujours dans l'interface Jeedom.
