# Post Developers' Lounge — Holmes MCP

> À publier sur community.jeedom.com, section Developers' Lounge, avant soumission market.
> Ce post est un prérequis au compte développeur / à la soumission — pas l'annonce grand public.

---

## [Plugin] Holmes MCP — Serveur MCP natif pour Jeedom

Bonjour à tous,

Je vous présente **Holmes MCP**, un plugin Jeedom open source qui expose votre box comme **serveur MCP** (Model Context Protocol) en lecture seule.

### À quoi ça sert ?

MCP est le protocole standard qui permet aux LLM (Claude, Cursor, etc.) d'interroger des sources de données externes. Holmes MCP transforme votre box Jeedom en source de données interrogeable directement depuis **Claude Desktop**, **Cursor** ou n'importe quel client MCP compatible — sans configuration côté client autre qu'une URL et un token Bearer.

Cas d'usage typiques :
- Auditer la configuration de sa box ("quels équipements sont désactivés ?", "quels scénarios utilisent cette commande ?")
- Diagnostiquer un comportement ("pourquoi ce scénario ne se déclenche pas ?")
- Assister à la conception ("explique-moi la structure de ce scénario")

### Caractéristiques techniques

- **26 tools MCP** en lecture seule : équipements, commandes, scénarios, plugins, logs, datastore, configuration, SQL restreint
- **5 resources MCP** : overview, health, scenario, equipment, logs du jour
- **Authentification Bearer** par utilisateur Jeedom (token stocké dans les options utilisateur)
- **Accès données** : MySQL via user dédié `jeedom_mcp_ro` (SELECT only) + API JSON-RPC localhost + logs fichier
- **Sanitisation forte** : liste blanche de champs + regex credentials + exclusions par plugin (25+ plugins couverts) — aucun credential exposé dans les réponses MCP
- **Daemon Python** (3.11+) — SDK MCP officiel, Streamable HTTP, spec 2025-03-26
- **Vue activité** dans l'interface Jeedom : tableau des derniers appels MCP avec filtre et rafraîchissement automatique
- **Protocole** : Streamable HTTP sur le port 8765 (configurable)
- **Licence** : AGPL-3.0

### Environnement cible

| Composant | Version |
|---|---|
| Jeedom | 4.5+ |
| OS | Debian 12 Bookworm x86_64 |
| Python | 3.11+ (installé via `system::update()`) |
| MariaDB | 10.x |

### Dépôt et documentation

- GitHub : https://github.com/Isilorn/holmesMcp
- Documentation : https://isilorn.github.io/holmesMcp/

### Statut

En bêta — validé sur box réelle Jeedom 4.5.3 (665 tests unitaires, tests d'intégration live).
Soumission market en bêta en cours de préparation.

N'hésitez pas si vous avez des questions sur l'implémentation ou la soumission market.

Isilorn
