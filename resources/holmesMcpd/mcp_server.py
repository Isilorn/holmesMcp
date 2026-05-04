"""Bootstrap du serveur MCP Holmes.

Construit l'instance FastMCP et enregistre les tools/resources.
J3-1 : Famille 1 — 4 tools découverte d'install.
J3-2 : Famille 2 — 7 tools équipements/commandes.
J3-3 : Famille 3 — 7 tools scénarios.
J5-1 : Familles 4-6 — 7 tools dataStore/logs/recherche.
J5-2 : Famille 7 — query_sql.
J5-4 : 5 resources (à venir).
"""

from __future__ import annotations

import argparse

import structlog
from _core import db as _db
from mcp.server.fastmcp import FastMCP
from tools import datastore, discovery, equipments, scenarios, search
from tools import logs as logs_tools
from tools import query_sql as query_sql_tools

log = structlog.get_logger('holmesMcp.server')

_INSTRUCTIONS = (
    'Holmes observe, déduit, raconte. '
    'Il expose votre installation Jeedom en lecture seule : équipements, commandes, '
    'scénarios, plugins, logs. '
    'Il ne modifie jamais votre installation. '
    'Posez vos questions sur votre maison connectée.'
)


def build_mcp(args: argparse.Namespace) -> FastMCP:
    """Construit et retourne l'instance FastMCP configurée."""
    mcp = FastMCP(
        name='Holmes MCP',
        instructions=_INSTRUCTIONS,
        host='0.0.0.0',
        port=args.port,
    )

    apikey = args.jeedom_apikey
    _register_family1(mcp)
    _register_family2(mcp, apikey)
    _register_family3(mcp, apikey)
    _register_family4(mcp)
    _register_family5(mcp)
    _register_family6(mcp)
    _register_family7(mcp)

    log.info('mcp_initialized', families=[1, 2, 3, 4, 5, 6, 7], tools=25)
    return mcp


def _register_family1(mcp: FastMCP) -> None:
    """Famille 1 — Découverte d'install (4 tools)."""

    @mcp.tool()
    def get_install_overview() -> dict:
        """Snapshot général de l'installation Jeedom.

        Retourne la version Jeedom, les comptages globaux d'équipements (actifs/total),
        scénarios (actifs/total), plugins, objets et commandes.
        """
        conn = _db.connect()
        try:
            return discovery.get_install_overview(conn)
        finally:
            conn.close()

    @mcp.tool()
    def list_objects() -> dict:
        """Hiérarchie des objets/pièces Jeedom.

        Retourne la liste des objets triée par ordre d'affichage, avec leur père
        (father_id) pour reconstituer la hiérarchie pièces/sous-pièces.
        isVisible indique si l'objet est affiché dans le dashboard.
        """
        conn = _db.connect()
        try:
            return discovery.list_objects(conn)
        finally:
            conn.close()

    @mcp.tool()
    def list_plugins() -> dict:
        """Plugins installés avec version et état.

        Retourne la liste des plugins installés sur cette box Jeedom.
        Le champ state indique si le daemon du plugin est opérationnel (ok/nok).
        logical_id est l'identifiant technique du plugin (ex. 'jMQTT', 'holmesMcp').
        """
        conn = _db.connect()
        try:
            return discovery.list_plugins(conn)
        finally:
            conn.close()

    @mcp.tool()
    def get_config(plugin: str | None = None, key_pattern: str | None = None) -> dict:
        """Configuration Jeedom par namespace plugin (sanitisée).

        Paramètres :
        - plugin      : namespace du plugin dans la table config
                        (ex. 'core', 'jMQTT', 'holmesMcp', 'agenda').
                        None ou '*' retourne tous les namespaces.
        - key_pattern : filtre LIKE optionnel sur la colonne key
                        (ex. 'mqtt%', '%port%') — None retourne toutes les clés

        Les valeurs dont la clé est sensible (token, password, apikey…) sont
        automatiquement masquées (***FILTERED***). La clé reste visible.
        Limite : 200 entrées par appel.
        """
        conn = _db.connect()
        try:
            return discovery.get_config(conn, plugin, key_pattern)
        finally:
            conn.close()


def _register_family2(mcp: FastMCP, apikey: str) -> None:
    """Famille 2 — Équipements et commandes (7 tools)."""

    @mcp.tool()
    def list_equipments(
        object_id: int | None = None,
        plugin: str | None = None,
        is_enable: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Liste des équipements filtrables par objet, plugin ou état actif.

        Paramètres :
        - object_id : filtre sur l'objet/pièce (id de la table object)
        - plugin     : filtre sur eqType_name (ex. 'jMQTT', 'thermostat')
        - is_enable  : True = uniquement les actifs, False = uniquement les désactivés
        - limit      : nombre max de résultats (max 100)
        - offset     : décalage pour la pagination

        Pour le détail d'un équipement (commandes + config), utilisez get_equipment.
        """
        conn = _db.connect()
        try:
            return equipments.list_equipments(conn, object_id, plugin, is_enable, limit, offset)
        finally:
            conn.close()

    @mcp.tool()
    def find_equipments_advanced(
        name_contains: str | None = None,
        object_id: int | None = None,
        plugin: str | None = None,
        is_enable: bool | None = None,
        generic_type: str | None = None,
        tags: str | None = None,
        limit: int = 50,
    ) -> dict:
        """Recherche avancée d'équipements avec filtres combinables.

        Paramètres :
        - name_contains : fragment de nom (insensible à la casse, LIKE %fragment%)
        - object_id     : filtre sur l'objet/pièce
        - plugin        : filtre sur eqType_name
        - is_enable     : True = actifs uniquement
        - generic_type  : type générique exact (ex. 'LIGHT', 'THERMOSTAT')
        - tags          : fragment de tag (LIKE %tag%)
        - limit         : max 50 résultats
        """
        conn = _db.connect()
        try:
            return equipments.find_equipments_advanced(
                conn, name_contains, object_id, plugin, is_enable, generic_type, tags, limit
            )
        finally:
            conn.close()

    @mcp.tool()
    def get_equipment(equipment_id: int) -> dict:
        """Détail complet d'un équipement : commandes, config sanitisée et valeurs courantes.

        Paramètres :
        - equipment_id : identifiant numérique de l'équipement (table eqLogic.id)

        Retourne l'équipement avec toutes ses métadonnées (configuration sanitisée,
        statut, tags) et la liste complète de ses commandes.
        Pour les commandes info, currentValue et collectDate indiquent la dernière
        valeur mesurée et sa date de collecte.
        Si l'équipement n'existe pas, retourne {'error': 'Équipement non trouvé'}.
        """
        conn = _db.connect()
        try:
            return equipments.get_equipment(conn, equipment_id, apikey)
        finally:
            conn.close()

    @mcp.tool()
    def find_equipment_by_name(name: str, limit: int = 10) -> dict:
        """Recherche un équipement par son nom (partiel, insensible à la casse).

        Paramètres :
        - name  : fragment de nom à rechercher
        - limit : max de résultats (par défaut 10, max 50)

        Exemple : name='salon' trouve 'Thermostat Salon', 'Prise Salon', etc.
        """
        conn = _db.connect()
        try:
            return equipments.find_equipment_by_name(conn, name, limit)
        finally:
            conn.close()

    @mcp.tool()
    def list_commands(
        equipment_id: int,
        cmd_type: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> dict:
        """Liste des commandes d'un équipement avec valeurs courantes.

        Paramètres :
        - equipment_id : identifiant de l'équipement (eqLogic.id)
        - cmd_type     : filtre optionnel sur le type ('info' ou 'action')
        - limit        : max 200 commandes
        - offset       : décalage pour la pagination

        Pour les commandes info, currentValue et collectDate indiquent la dernière
        valeur mesurée et sa date de collecte.
        Pour la recherche transverse de commandes, utilisez find_commands_advanced.
        """
        conn = _db.connect()
        try:
            return equipments.list_commands(conn, equipment_id, cmd_type, limit, offset, apikey)
        finally:
            conn.close()

    @mcp.tool()
    def find_commands_advanced(
        name_contains: str | None = None,
        equipment_id: int | None = None,
        cmd_type: str | None = None,
        subtype: str | None = None,
        generic_type: str | None = None,
        is_historized: bool | None = None,
        limit: int = 50,
    ) -> dict:
        """Recherche avancée de commandes avec filtres combinables.

        Paramètres :
        - name_contains : fragment de nom (LIKE %fragment%)
        - equipment_id  : restreindre à un équipement
        - cmd_type      : 'info' ou 'action'
        - subtype       : sous-type (ex. 'numeric', 'binary', 'string', 'slider', 'message')
        - generic_type  : type générique (ex. 'TEMPERATURE', 'HUMIDITY', 'LIGHT_STATE')
        - is_historized : True = uniquement les commandes historisées
        - limit         : max 50 résultats
        """
        conn = _db.connect()
        try:
            return equipments.find_commands_advanced(
                conn, name_contains, equipment_id, cmd_type,
                subtype, generic_type, is_historized, limit,
            )
        finally:
            conn.close()

    @mcp.tool()
    def get_command_history(cmd_id: int, limit: int = 100) -> dict:
        """Historique d'une commande info : récent (history) + archivé (historyArch).

        Paramètres :
        - cmd_id : identifiant de la commande (cmd.id)
        - limit  : max de lignes par table (défaut 100, max 100)

        Retourne deux listes séparées triées par datetime décroissant :
        - history_recent   : entrées de la table history (plus récentes)
        - history_archived : entrées de la table historyArch (plus anciennes)
        """
        conn = _db.connect()
        try:
            return equipments.get_command_history(conn, cmd_id, limit)
        finally:
            conn.close()


def _register_family3(mcp: FastMCP, apikey: str) -> None:
    """Famille 3 — Scénarios (7 tools)."""

    @mcp.tool()
    def list_scenarios(
        group: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Liste des scénarios avec état runtime (state, lastLaunch).

        Paramètres :
        - group     : filtre exact sur le groupe du scénario
        - is_active : True = uniquement les actifs, False = uniquement les désactivés
        - limit     : nombre max de résultats (max 100)
        - offset    : décalage pour la pagination

        Champs runtime enrichis via API JSON-RPC :
        - state     : état d'exécution ('run', 'stop', 'error', 'in progress')
        - lastLaunch : datetime du dernier déclenchement

        Pour le détail d'un scénario (déclencheurs, structure), utilisez get_scenario.
        """
        conn = _db.connect()
        try:
            return scenarios.list_scenarios(conn, group, is_active, limit, offset, apikey)
        finally:
            conn.close()

    @mcp.tool()
    def find_scenarios_advanced(
        name_contains: str | None = None,
        group: str | None = None,
        is_active: bool | None = None,
        mode: str | None = None,
        trigger_type: str | None = None,
        limit: int = 50,
    ) -> dict:
        """Recherche avancée de scénarios avec filtres combinables et état runtime.

        Paramètres :
        - name_contains : fragment de nom (insensible à la casse, LIKE %fragment%)
        - group         : filtre exact sur le groupe
        - is_active     : True = actifs uniquement
        - mode          : filtre exact sur le mode ('schedule', 'provoke', 'all')
        - trigger_type  : fragment dans le champ trigger (ex. 'schedule', 'event')
        - limit         : max 50 résultats

        Champs runtime enrichis via API JSON-RPC : state, lastLaunch.
        """
        conn = _db.connect()
        try:
            return scenarios.find_scenarios_advanced(
                conn, name_contains, group, is_active, mode, trigger_type, limit, apikey
            )
        finally:
            conn.close()

    @mcp.tool()
    def get_scenario(scenario_id: int) -> dict:
        """Détail complet d'un scénario : métadonnées, déclencheurs, état runtime.

        Paramètres :
        - scenario_id : identifiant numérique du scénario (table scenario.id)

        Retourne les métadonnées complètes du scénario (sanitisées) enrichies avec :
        - state      : état d'exécution ('run', 'stop', 'error', 'in progress')
        - lastLaunch : datetime du dernier déclenchement

        Ces champs proviennent de l'API JSON-RPC (absents de la base MySQL).
        Pour le log du dernier run, utilisez get_scenario_log(scenario_id).
        Pour l'arbre structurel, utilisez get_scenario_structure.
        Pour la description LLM-friendly, utilisez describe_scenario.
        Si le scénario n'existe pas, retourne {'error': 'Scénario non trouvé'}.
        """
        conn = _db.connect()
        try:
            return scenarios.get_scenario(conn, scenario_id, apikey)
        finally:
            conn.close()

    @mcp.tool()
    def get_scenario_structure(
        scenario_id: int,
        max_depth: int = 3,
        follow_scenario_calls: int = 0,
    ) -> dict:
        """Arbre structurel brut d'un scénario (machine-friendly).

        Paramètres :
        - scenario_id           : identifiant du scénario
        - max_depth             : profondeur max de récursion des éléments (défaut 3)
        - follow_scenario_calls : niveaux de suivi des appels inter-scénarios (0 = désactivé)

        Retourne l'arbre de scenarioElement/scenarioSubElement/scenarioExpression.
        Pour une description lisible avec résolution des #[O][E][C]#, utilisez describe_scenario.
        """
        conn = _db.connect()
        try:
            return scenarios.get_scenario_structure(
                conn, scenario_id, max_depth, follow_scenario_calls
            )
        finally:
            conn.close()

    @mcp.tool()
    def describe_scenario(scenario_id: int) -> dict:
        """Description LLM-friendly d'un scénario avec résolution systématique des #[O][E][C]#.

        Paramètres :
        - scenario_id : identifiant du scénario

        Résout automatiquement toutes les références #cmdId# en #[Objet][Équipement][Commande]#
        dans les déclencheurs et les expressions du scénario.
        Enrichit aussi avec state et lastLaunch via API JSON-RPC.
        Pour l'arbre brut (machine-friendly), utilisez get_scenario_structure.
        """
        conn = _db.connect()
        try:
            return scenarios.describe_scenario(conn, scenario_id, apikey)
        finally:
            conn.close()

    @mcp.tool()
    def find_scenario_dependencies(scenario_id: int) -> dict:
        """Callers d'un scénario : quels scénarios l'appellent via scenario/start.

        Paramètres :
        - scenario_id : identifiant du scénario

        Retourne les scénarios qui appellent ce scénario (callers).
        Pour voir les scénarios appelés par ce scénario (callees), utiliser
        get_scenario_structure(scenario_id, follow_scenario_calls=1).
        """
        conn = _db.connect()
        try:
            return scenarios.find_scenario_dependencies(conn, scenario_id)
        finally:
            conn.close()

    @mcp.tool()
    def get_scenario_log(scenario_id: int, lines: int = 100) -> dict:
        """Log du dernier run d'un scénario.

        Paramètres :
        - scenario_id : identifiant du scénario
        - lines       : nombre de lignes à retourner (défaut 100, max 500)

        Les logs de scénario sont stockés dans scenarioLog/scenario<id>.log.
        Retourne {'error': ...} si le fichier n'existe pas.
        """
        conn = _db.connect()
        try:
            return scenarios.get_scenario_log(conn, scenario_id, lines)
        finally:
            conn.close()


def _register_family4(mcp: FastMCP) -> None:
    """Famille 4 — Variables / dataStore (2 tools)."""

    @mcp.tool()
    def list_datastore_variables(
        var_type: str | None = None,
        link_id: int | None = None,
        key_pattern: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Variables persistantes Jeedom (table dataStore).

        Paramètres :
        - var_type    : filtre exact sur le type ('global' ou 'scenario')
        - link_id     : filtre sur l'identifiant lié (0 pour global, scenario_id pour scenario)
        - key_pattern : filtre LIKE sur le nom de variable (ex. 'meteo%', '%temp%')
        - limit       : nombre max de résultats (max 200)
        - offset      : décalage pour la pagination

        Les variables globales ont type='global' et link_id=0.
        Les variables de scénario ont type='scenario' et link_id=<scenario_id>.
        """
        conn = _db.connect()
        try:
            return datastore.list_datastore_variables(
                conn, var_type, link_id, key_pattern, limit, offset
            )
        finally:
            conn.close()

    @mcp.tool()
    def get_datastore_variable(
        key: str,
        var_type: str | None = None,
        link_id: int | None = None,
    ) -> dict:
        """Valeur courante d'une variable dataStore par nom de clé.

        Paramètres :
        - key      : nom exact de la variable (ex. 'temperature_salon', 'alarme_active')
        - var_type : restreindre au type ('global' ou 'scenario') si ambiguïté
        - link_id  : restreindre à un scenario_id si var_type='scenario'

        Retourne {'error': ...} si la variable n'existe pas.
        Si plusieurs variables partagent le même nom (global + scenario), retourne la liste.
        """
        conn = _db.connect()
        try:
            return datastore.get_datastore_variable(conn, key, var_type, link_id)
        finally:
            conn.close()


def _register_family5(mcp: FastMCP) -> None:
    """Famille 5 — Logs et diagnostic (3 tools)."""

    @mcp.tool()
    def list_log_files() -> dict:
        """Liste des fichiers de log Jeedom disponibles avec taille et date de modification.

        Retourne tous les logs accessibles dans les répertoires Jeedom connus.
        Le champ name de chaque entrée est utilisable directement avec tail_log.
        Les fichiers de sous-répertoires (ex. scenarioLog/scenario70.log) sont inclus.
        """
        return logs_tools.list_log_files()

    @mcp.tool()
    def tail_log(
        log_name: str,
        lines: int = 100,
        grep: str | None = None,
    ) -> dict:
        """Tail d'un log Jeedom avec grep optionnel.

        Paramètres :
        - log_name : nom du fichier de log (ex. 'core', 'jMQTT', 'scenarioLog/scenario70.log')
                     Utiliser list_log_files pour connaître les noms disponibles.
        - lines    : nombre de lignes depuis la fin (défaut 100, max 500)
        - grep     : filtre optionnel — seules les lignes contenant ce texte sont retournées
                     (insensible à la casse)

        Retourne {'log_file': ..., 'lines': [...], 'count': N}.
        Retourne {'error': ..., 'lines': [], 'count': 0} si le log est introuvable.
        """
        return logs_tools.tail_log(log_name, lines, grep)

    @mcp.tool()
    def get_health_summary() -> dict:
        """Résumé de santé Jeedom : daemons KO, messages système non lus, crons bloqués.

        Interroge trois sources MySQL :
        - plugins_nok       : plugins avec daemon en panne (status='nok')
        - messages_unread   : messages système non lus (20 plus récents)
        - crons_running     : crons actuellement en état running (potentiellement bloqués)

        Si toutes les listes sont vides, l'installation est en bonne santé.
        Le champ summary fournit les comptages globaux.
        """
        conn = _db.connect()
        try:
            return logs_tools.get_health_summary(conn)
        finally:
            conn.close()


def _register_family6(mcp: FastMCP) -> None:
    """Famille 6 — Recherche transverse (1 tool)."""

    @mcp.tool()
    def search_text(text: str, limit: int = 20) -> dict:
        """Recherche d'une chaîne dans noms d'équipements, commandes, scénarios et expressions.

        Paramètres :
        - text  : texte à rechercher (minimum 2 caractères, insensible à la casse)
        - limit : nombre max de résultats par catégorie (défaut 20, max 50)

        Retourne quatre catégories : equipements, commandes, scenarios, expressions.
        Le champ expressions est particulièrement utile pour retrouver les scénarios
        qui utilisent une commande donnée (chercher '#[Objet][Équipement][Commande]#').

        Exemple : search_text('salon') retrouve 'Prise Salon' (équipement),
        'Lumière Salon ON' (commande), 'Réveil Salon' (scénario).
        """
        conn = _db.connect()
        try:
            return search.search_text(conn, text, limit)
        finally:
            conn.close()


def _register_family7(mcp: FastMCP) -> None:
    """Famille 7 — Requête SQL libre (1 tool)."""

    @mcp.tool()
    def query_sql(sql: str) -> dict:
        """Exécute une requête SELECT libre sur la base Jeedom (lecture seule).

        Réservé aux requêtes que les autres tools ne couvrent pas.
        Pour les cas courants, préférer les tools dédiés (list_equipments,
        list_scenarios, search_text, etc.) qui sont plus sûrs et plus rapides.

        SÉCURITÉ : SELECT uniquement, tables sensibles bloquées, LIMIT injecté
        si absent (50), plafonné à 200. Résultats sanitisés (D15.1/D15.3).

        Tables utiles : eqLogic, cmd, scenario, object, dataStore, config,
        history, historyArch, plugin, update, message, cron.

        Mots réservés à backticker : `trigger`, `repeat`, `update`.

        Exemples :
        - SELECT id, name FROM eqLogic WHERE object_id = 3
        - SELECT datetime, value FROM history WHERE cmd_id = 12 ORDER BY datetime DESC
        - SELECT key, value FROM dataStore WHERE type = 'scenario' AND link_id = 5
        """
        conn = _db.connect()
        try:
            return query_sql_tools.query_sql(conn, sql)
        finally:
            conn.close()
