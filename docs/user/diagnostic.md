# Diagnostic & Logs

## Vue Activité MCP

La page de configuration du plugin (**Plugins → Supervision → Holmes MCP**) propose un onglet **Activité MCP** : tableau des dernières requêtes reçues par le daemon, avec :

- **Tool invoqué** — nom du tool ou de la resource
- **Statut** — succès (✅) ou erreur (❌)
- **Horodatage** — date et heure de la requête
- **Durée** — temps d'exécution en ms

Le tableau se rafraîchit automatiquement toutes les **30 secondes**.

## Logs du plugin

Les logs du daemon Holmes MCP sont accessibles depuis l'interface Jeedom standard :

**Analyse → Logs → holmesMcp**

Les niveaux de log configurables sont : `Debug`, `Info`, `Warning`, `Error`. En cas de problème, passez en `Debug` pour obtenir le détail complet des requêtes.

## Logs depuis un tool MCP

Depuis un client MCP connecté, vous pouvez aussi consulter les logs :

```
# Lister les logs disponibles
list_log_files()

# Lire le log du daemon Holmes MCP
tail_log(log_name="holmesMcp", lines=100)

# Filtrer sur les erreurs
tail_log(log_name="holmesMcp", lines=200, grep="error")
```

## Problèmes courants

### Le daemon ne démarre pas

**Symptôme :** pastille rouge, message "KO" dans la page du plugin.

**Vérifications :**

1. Port 8765 déjà occupé :

    ```bash
    ss -tlnp | grep 8765
    ```

    Si le port est pris, changez-le dans la configuration du plugin.

2. Dépendances Python non installées :

    ```bash
    ls /var/www/html/plugins/holmesMcp/resources/python_venv/bin/python3
    ```

    Si absent, relancez l'installation des dépendances.

3. Fichier de configuration MySQL manquant :

    ```bash
    cat /etc/holmes_mcp_ro.conf
    ```

    Si absent, reprenez l'[étape 3 de l'installation](installation.md#etape-3-creer-lutilisateur-mysql-en-lecture-seule).

4. Consulter les logs Jeedom :

    **Analyse → Logs → holmesMcp** (passer en niveau `Debug` si nécessaire).

---

### 401 Unauthorized

**Symptôme :** le client MCP retourne une erreur 401.

**Cause :** token Bearer absent, invalide ou révoqué.

**Solution :** vérifiez que le header `Authorization: Bearer <token>` est correctement configuré dans votre client. Régénérez un token si nécessaire depuis la page du plugin.

---

### Connection refused

**Symptôme :** le client ne peut pas se connecter à `http://<ip-box>:8765/mcp`.

**Vérifications :**

1. Le daemon est-il démarré ? (pastille verte dans la page du plugin)
2. L'IP et le port dans la config client correspondent-ils à ceux de la box ?
3. La box est-elle accessible depuis le client ? (même réseau LAN ou VPN)

---

### MySQL inaccessible

**Symptôme :** erreur dans les logs : `Can't connect to MySQL server` ou `Access denied for user 'jeedom_mcp_ro'`.

**Vérifications :**

1. L'utilisateur MySQL existe :

    ```bash
    sudo mysql -e "SELECT User, Host FROM mysql.user WHERE User='jeedom_mcp_ro';"
    ```

2. Le fichier de config est lisible par le daemon (user `www-data`) :

    ```bash
    ls -la /etc/holmes_mcp_ro.conf
    # Doit afficher : -rw-r----- root www-data
    ```

---

### Données manquantes ou incomplètes

**Symptôme :** un équipement ou scénario n'apparaît pas dans les résultats.

**Causes possibles :**

- Équipement désactivé → utilisez `is_enable=null` pour inclure les inactifs dans `list_equipments`
- Limite de pagination atteinte → augmentez `limit` ou utilisez `offset`
- Équipement dans un objet non inclus → retirez le filtre `object_id`

---

## Commandes de diagnostic utiles (SSH)

```bash
# Statut du daemon
ps aux | grep holmesMcpd

# Port d'écoute
ss -tlnp | grep 8765

# Logs en temps réel
tail -f /var/log/jeedom/holmesMcp.log

# Test connexion MySQL
mysql -u jeedom_mcp_ro -p -h localhost jeedom -e "SELECT 1;"
```
