# Installation

## Prérequis

| Prérequis | Version minimale | Notes |
| --- | --- | --- |
| Jeedom | 4.5 | Requis pour `system::update()` venv Python |
| Debian | 12 (Bookworm) | Python 3.11 natif |
| Python | 3.11 | Fourni par Bookworm |
| Port | 8765 | Doit être libre sur la box |
| MariaDB | 10.x | Standard Jeedom Bookworm |

!!! warning "Bookworm requis"
    Holmes MCP a été développé et testé sur Debian 12 (Bookworm). Une installation sur Bullseye (Debian 11) ou Buster n'est pas supportée.

## Étape 1 — Installer le plugin depuis le market

1. Dans Jeedom, allez dans **Plugins → Gestion des plugins**
2. Cliquez sur **Market** et recherchez **Holmes MCP**
3. Installez le plugin (branche **stable** ou **bêta** selon votre préférence)
4. Activez le plugin

## Étape 2 — Installer les dépendances Python

1. Ouvrez la page de configuration du plugin (**Plugins → Supervision → Holmes MCP**)
2. Cliquez sur **Installer / Mettre à jour les dépendances**
3. Attendez la fin de l'installation (suivez les logs en bas de page)

Les dépendances s'installent dans un **virtualenv isolé** (`resources/python_venv/`) géré par Jeedom. Aucune dépendance système n'est modifiée.

## Étape 3 — Créer l'utilisateur MySQL en lecture seule

!!! info "Étape manuelle — une seule fois"
    Cette étape est requise une seule fois, au moment de l'installation initiale. Elle crée un utilisateur MySQL `jeedom_mcp_ro` avec des droits `SELECT` uniquement.

Connectez-vous en SSH à votre box Jeedom, puis exécutez :

```bash
sudo mysql
```

Dans la console MySQL :

```sql
CREATE USER 'jeedom_mcp_ro'@'localhost' IDENTIFIED BY 'votre_mot_de_passe_ro';
GRANT SELECT ON jeedom.* TO 'jeedom_mcp_ro'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

!!! tip "Choisissez un mot de passe fort"
    Ce mot de passe sera stocké dans `/etc/holmes_mcp_ro.conf` sur votre box. Il ne quitte jamais la box.

Créez ensuite le fichier de configuration MySQL :

```bash
sudo nano /etc/holmes_mcp_ro.conf
```

Contenu du fichier :

```ini
[mysql]
host = localhost
port = 3306
user = jeedom_mcp_ro
password = votre_mot_de_passe_ro
database = jeedom
```

Sécurisez les permissions :

```bash
sudo chmod 640 /etc/holmes_mcp_ro.conf
sudo chown root:www-data /etc/holmes_mcp_ro.conf
```

## Étape 4 — Démarrer le daemon

1. Retournez dans la page de configuration du plugin
2. Activez et démarrez le daemon Holmes MCP
3. Vérifiez que le statut passe à **OK** (pastille verte)

Si le daemon ne démarre pas, consultez la section [Diagnostic & logs](diagnostic.md).

## Vérification

Une fois le daemon démarré, vous pouvez vérifier qu'il répond correctement :

```bash
curl http://localhost:8765/mcp
```

La réponse doit être une réponse HTTP valide (le protocole MCP nécessite un client MCP pour une interaction complète).

## Mise à jour

Les mises à jour du plugin se font depuis le market Jeedom (bouton **Mettre à jour**). Le daemon redémarre automatiquement après mise à jour. Aucune manipulation manuelle de l'utilisateur MySQL n'est nécessaire lors des mises à jour.

## Désinstallation

1. Arrêtez le daemon depuis la page de configuration
2. Désinstallez le plugin depuis le market
3. (Optionnel) Supprimez l'utilisateur MySQL :

```sql
sudo mysql -e "DROP USER 'jeedom_mcp_ro'@'localhost';"
```

4. (Optionnel) Supprimez `/etc/holmes_mcp_ro.conf`
