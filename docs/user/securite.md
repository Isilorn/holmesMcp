# Sécurité

La sécurité est un pilier de conception de Holmes MCP, pas un ajout a posteriori. Cette page détaille les mécanismes en place.

## Lecture seule (V1)

Holmes MCP est **architecturalement** en lecture seule :

- L'utilisateur MySQL `jeedom_mcp_ro` a uniquement `GRANT SELECT` — il est **impossible** d'écrire en base
- L'API JSON-RPC est utilisée en lecture uniquement — 12 verbes d'écriture sont blacklistés dans le code (`scenarion::changeState`, `cmd::execCmd`, etc.)
- Aucun tool n'expose de point d'entrée d'écriture

## Authentification Bearer

Chaque requête doit porter un token Bearer valide dans le header HTTP :

```
Authorization: Bearer <votre-token>
```

Le token est lié à un utilisateur Jeedom. Sans token valide, le daemon retourne `401 Unauthorized` et ignore la requête.

Les tokens sont stockés dans la base Jeedom via `User->setOption()` — ils ne transitent jamais en clair dans les logs du daemon.

## Sanitisation des données

Holmes MCP applique **3 mécanismes cumulés** pour éviter toute fuite de credential via les données retournées.

### Mécanisme 1 — Whitelist de champs

Seuls les champs autorisés d'un équipement ou d'une commande sont retournés. Les champs `configuration`, `cache`, et tout champ non listé sont exclus par défaut.

### Mécanisme 2 — Regex sur patterns sensibles

Les valeurs retournées sont scannées par des expressions régulières détectant les patterns de credentials connus :

- Clés API (format `[a-f0-9]{40,}`)
- Tokens JWT
- Mots de passe courants (champs nommés `password`, `passwd`, `secret`, `apikey`…)
- Adresses MAC complètes
- Numéros de téléphone

Tout champ correspondant est remplacé par `***FILTERED***`.

### Mécanisme 3 — Hard-code par plugin

Certains plugins stockent des credentials avec des noms de champs non-génériques. Holmes MCP maintient une liste de champs supplémentaires à filtrer par plugin :

| Plugin | Champs filtrés |
| --- | --- |
| jMQTT | `mqttUser`, `mqttPass`, `mqttTlsClientKey`, `mqttTlsClientCert` |
| JeedomConnect | `apiKey`, `token`, `installCode` |
| Aqara | `password`, `countryCode` |
| Zigbee2MQTT | `key` |
| Et autres… | Voir ADR-0017 |

!!! tip "Vérification"
    En cas de doute sur un champ, utilisez `get_equipment` sur un équipement concerné et vérifiez que les credentials sont bien filtrés avant de partager le résultat avec un LLM.

## Isolation réseau

- Le daemon écoute uniquement sur le port configuré (défaut 8765) — **pas d'exposition automatique sur Internet**
- MySQL est accédé uniquement via socket Unix localhost
- L'API JSON-RPC est appelée uniquement sur `localhost` — elle n'est pas exposée à l'extérieur

## query_sql — Sécurité renforcée

Le tool `query_sql` permet des requêtes SQL libres mais avec des garde-fous stricts :

- **SELECT uniquement** — toute requête non-SELECT est rejetée
- **Blacklist de tables** — les tables `user`, `session`, `network` et autres tables sensibles sont interdites
- **Blacklist de colonnes** — les colonnes `password`, `api`, `token` et similaires sont détectées et bloquées
- **LIMIT plafonné** — toute requête reçoit un `LIMIT` automatique (max 200 lignes)
- **Sanitisation appliquée** — les 3 mécanismes s'appliquent aussi aux résultats SQL

!!! warning "Usage de query_sql"
    `query_sql` est un outil avancé destiné aux utilisateurs qui connaissent le schéma Jeedom. En cas de doute, préférez les tools spécialisés (`get_equipment`, `list_scenarios`…) qui sont plus sûrs et plus simples.

## Isolation des credentials du repo

Le code source Holmes MCP (GitHub) **ne contient aucun credential** :

- Aucune IP, hostname, mot de passe, token, clé API dans le code
- `.gitignore` strict + hooks pre-commit/pre-push avec scan automatique de patterns sensibles
- La configuration sensible reste exclusivement sur la box (`/etc/holmes_mcp_ro.conf`)
