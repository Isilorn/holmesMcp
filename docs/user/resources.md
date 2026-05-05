# Resources (5)

Holmes MCP expose **5 resources** accessibles via des URI `jeedom://`. Les resources MCP sont des points de données que le client peut lire directement, sans invoquer un tool.

## Différence resource vs tool

| | Resource | Tool |
| --- | --- | --- |
| Accès | URI fixe | Appel avec paramètres |
| Usage typique | Vue de départ, contexte | Requête ciblée |
| Cache client | Possible | Non |

Les resources sont utiles pour obtenir rapidement un aperçu sans avoir à formuler une requête tool.

---

## `jeedom://install/overview`

Vue d'ensemble de l'installation Jeedom.

**Contenu :** version Jeedom, comptages globaux (équipements, commandes actives, scénarios, plugins installés, objets).

**Équivalent tool :** `get_install_overview`

**Exemple d'usage :** Contexte d'ouverture de session — "Qu'est-ce que j'ai sur cette box ?"

---

## `jeedom://install/health`

État de santé du système.

**Contenu :** liste des plugins avec daemon KO, messages système récents, crons daemon actifs.

**Équivalent tool :** `get_health_summary`

**Exemple d'usage :** Vérification rapide — "Tout va bien sur la box ?"

---

## `jeedom://scenario/{id}`

Détail complet d'un scénario spécifique.

**Paramètre :** `{id}` — identifiant numérique du scénario.

**Contenu :** description lisible (résolution des références `#[Objet][Équipement][Commande]#`) + log du dernier run (50 dernières lignes).

**Équivalent tool :** combine `describe_scenario` + `get_scenario_log`

**Exemple d'usage :** `jeedom://scenario/42` — contexte complet du scénario 42 en une seule lecture.

---

## `jeedom://equipment/{id}`

Détail complet d'un équipement spécifique.

**Paramètre :** `{id}` — identifiant numérique de l'équipement.

**Contenu :** configuration de l'équipement (champs sensibles sanitisés), liste de ses commandes avec état temps réel.

**Équivalent tool :** `get_equipment`

**Exemple d'usage :** `jeedom://equipment/15` — tout savoir sur l'équipement 15 immédiatement.

---

## `jeedom://logs/today`

Logs Jeedom du jour (log `http`, 500 dernières lignes).

**Contenu :** les 500 dernières lignes du log principal Jeedom (`http`).

**Équivalent tool :** `tail_log(log_name="http", lines=500)`

**Exemple d'usage :** Diagnostic rapide — "Qu'est-ce qui s'est passé aujourd'hui sur Jeedom ?"

---

## Usage dans les clients MCP

Les resources sont accessibles depuis les clients MCP qui les supportent. Dans Claude Desktop par exemple, vous pouvez référencer une resource dans votre prompt en utilisant son URI.

!!! info "Support variable selon les clients"
    Tous les clients MCP ne supportent pas les resources de la même façon. Claude Code et MCP Inspector offrent le meilleur support. Consultez la documentation de votre client.
