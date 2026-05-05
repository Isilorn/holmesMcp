# Configuration

## Page de configuration du plugin

Accédez à la configuration via **Plugins → Supervision → Holmes MCP**.

### Paramètres disponibles

| Paramètre | Défaut | Description |
| --- | --- | --- |
| Port daemon | `8765` | Port HTTP d'écoute du serveur MCP |
| Niveau de log | `Info` | Verbosité des logs daemon (`Debug`, `Info`, `Warning`, `Error`) |

!!! note "Port 8765"
    Le port 8765 est le port par défaut. S'il est déjà occupé par un autre service, modifiez-le avant de démarrer le daemon. Communiquez le port choisi dans l'URL de votre client MCP.

### Statut du daemon

La pastille sur la page de configuration indique l'état du daemon :

- **Vert (OK)** — daemon actif, prêt à recevoir des connexions
- **Orange** — daemon en cours de démarrage
- **Rouge (KO)** — daemon arrêté ou en erreur → voir [Diagnostic & logs](diagnostic.md)

## Générer un token Bearer

Chaque utilisateur Jeedom dispose de son propre token d'accès. Le token est lié à un compte Jeedom et hérite de ses droits de lecture.

### Depuis la page de configuration du plugin

1. Dans la page du plugin, cliquez sur **Gérer les tokens**
2. Sélectionnez l'utilisateur Jeedom concerné
3. Cliquez sur **Générer un token**
4. Copiez le token — il ne sera affiché qu'une seule fois

!!! warning "Confidentialité du token"
    Le token Bearer donne accès en lecture à toute votre installation Jeedom (équipements, scénarios, logs). Traitez-le comme un mot de passe :

    - Ne le partagez pas
    - Ne le commitez pas dans un dépôt git
    - Régénérez-le immédiatement en cas de compromission

### Révoquer un token

Pour révoquer un token, retournez dans **Gérer les tokens** et supprimez le token de l'utilisateur concerné. Un nouveau token peut être généré à tout moment.

### Un token par utilisateur

Chaque utilisateur Jeedom a un token distinct. Cela permet de :

- Restreindre l'accès à certains utilisateurs seulement
- Révoquer l'accès d'un utilisateur sans impacter les autres
- Tracer les accès par utilisateur dans les logs

## URL du serveur MCP

L'URL à communiquer à votre client MCP est :

```text
http://<ip-de-votre-box>:8765/mcp
```

Remplacez `<ip-de-votre-box>` par l'adresse IP LAN de votre box Jeedom (ex. `203.0.113.10`).

!!! info "Accès LAN uniquement (V1)"
    Holmes MCP V1 écoute uniquement sur le réseau local (HTTP, pas HTTPS). Il n'est pas prévu pour une exposition sur Internet. Utilisez un VPN pour accéder à votre box à distance.

## Vue activité MCP

La page de configuration propose un onglet **Activité MCP** qui affiche un journal des dernières requêtes reçues par le daemon : tool invoqué, statut (succès/erreur), horodatage. Ce tableau se rafraîchit automatiquement toutes les 30 secondes.

Voir [Diagnostic & logs](diagnostic.md) pour plus de détails sur l'utilisation de cette vue.
