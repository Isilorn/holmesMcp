"""Sanitisation des données Jeedom avant exposition MCP (D15.1-D15.6).

3 mécanismes cumulatifs (défense en profondeur) :
  1. Whitelist de champs exposables par table connue — tout champ absent → masqué
  2. Regex sur clés JSON des blobs configuration/options
  3. Champs exotiques hard-codés par plugin (nommages non couverts par la regex)

Comportement : mask + count — valeur remplacée par FILTERED, _filtered_fields
joint à chaque réponse pour transparence LLM-side (D15.1).

Cas spécial table config : la colonne key reste visible, la colonne value est
masquée si key matche la regex (le LLM sait que le champ existe et peut
l'expliquer à l'utilisateur).

Couverture tests : 100% obligatoire (ADR-0017, D15.5).
Dérivé de jeedom-audit/_common/sensitive_fields.py — étendu (3 mécanismes).
"""

from __future__ import annotations

import json
import re
from typing import Any

FILTERED = '***FILTERED***'

# --- Mécanisme 2 : regex sur clés JSON des blobs ---
# Source : D15.2 — liste figée V1, enrichissement via ADR en V1.x+
_BLOB_KEY_RE = re.compile(
    r'(?i)(password|pwd|token|apikey|api_key|secret|hash|credentials|auth|'
    r'cert|private_key|access_key|client_secret|bearer)'
)

# --- Mécanisme 2bis : segmentation de l'identifiant en MOTS ---
# `key` et `api` ne peuvent pas entrer dans _BLOB_KEY_RE en sous-chaîne : ils
# attraperaient `monkey`, `keyboard`, `rapide`. On segmente donc l'identifiant sur
# les frontières camelCase, `_`, `::`, `-`, `.` et les chiffres, puis on teste chaque MOT.
# Trouvé à l'audit B3 (2026-09-08) : `keyGMG`, `keyNavitia`, `jawglabKey` sortaient en
# clair parce que la regex ne porte que `apikey`/`api_key`/`access_key`/`private_key`.
_WORD_SPLIT_RE = re.compile(r'[^A-Za-z]+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')

# Mots dont la seule présence suffit : une clé nommée « key » EST une clé.
_SECRET_WORDS = frozenset({'key'})

# Clés dont seule la correspondance EXACTE compte. `api` est la clé d'API de plugin
# Jeedom ; en mot, il masquerait `apiUrl` et `apiVersion`, qui ne sont pas des secrets.
_SECRET_EXACT_KEYS = frozenset({'api'})


def _key_words(key: str) -> set[str]:
    """Segmente un identifiant en mots minuscules (camelCase, _, ::, -, ., chiffres)."""
    return {w.lower() for w in _WORD_SPLIT_RE.split(key) if w}


# --- Mécanisme 1 : whitelist de champs exposables par table connue ---
# Colonnes "blob" incluses dans la whitelist ; leur contenu JSON passe ensuite
# en mécanisme 2+3. Tout champ absent → masqué.
_TABLE_WHITELISTS: dict[str, frozenset[str]] = {
    'eqLogic': frozenset(
        {
            'id',
            'name',
            'eqType_name',
            'object_id',
            'isEnable',
            'isVisible',
            'logicalId',
            'generic_type',
            'order',
            'tags',
            'category',
            'timeout',
            'comment',
            'status',
            'configuration',
        }
    ),
    'cmd': frozenset(
        {
            'id',
            'name',
            'eqLogic_id',
            'type',
            'subType',
            'logicalId',
            'generic_type',
            'isVisible',
            'unite',
            'isHistorized',
            'display',
            'order',
            'value',
            'configuration',
            'template',
            'currentValue',
            'collectDate',
        }
    ),
    'scenario': frozenset(
        {
            'id',
            'name',
            'state',
            'isActive',
            'mode',
            'type',
            'lastLaunch',
            'description',
            'group',
            'order',
            'timeout',
            'trigger',
            'real_trigger',
        }
    ),
    'object': frozenset(
        {
            'id',
            'name',
            'father_id',
            'isVisible',
            'position',
        }
    ),
    'dataStore': frozenset(
        {
            'id',
            'type',
            'link_id',
            'key',
            'value',
        }
    ),
    'config': frozenset(
        {
            'plugin',
            'key',
            'value',
        }
    ),
    'plugin': frozenset(
        {
            'id',
            'name',
            'version',
            'remote_version',
            'state',
            'logical_id',
        }
    ),
    'history': frozenset(
        {
            'cmd_id',
            'datetime',
            'value',
        }
    ),
    'historyArch': frozenset(
        {
            'cmd_id',
            'datetime',
            'value',
        }
    ),
    'scenarioElement': frozenset(
        {
            'id',
            'scenario_id',
            'type',
            'order',
        }
    ),
    'scenarioSubElement': frozenset(
        {
            'id',
            'element_id',
            'type',
            'order',
            'options',
        }
    ),
    'scenarioExpression': frozenset(
        {
            'id',
            'scenarioSubElement_id',
            'type',
            'order',
            'expression',
            'options',
        }
    ),
    'interactDef': frozenset(
        {
            'id',
            'query',
            'reply',
            'isEnable',
            'group',
        }
    ),
}

# Colonnes dont le contenu est parsé comme JSON pour appliquer mech 2+3
_BLOB_COLUMNS: frozenset[str] = frozenset({'configuration', 'options'})

# --- Mécanisme 3 : champs exotiques hard-codés par plugin (D15.2, D15.2 enrichi J2) ---
# Nommages spécifiques non couverts par _BLOB_KEY_RE.
# Liste V1 : 10 plugins initiaux (D15.2 J1-1) + 5 plugins install PO (J2-1).
_PLUGIN_EXTRA_KEYS: dict[str, frozenset[str]] = {
    # Plugins install PO — eqType_name et champs vérifiés live J6-2
    'jMQTT': frozenset(
        {
            # Vrais champs camelCase broker (vérifiés live J6-2 — non couverts par regex mech 2)
            'mqttUser',
            'mqttPass',
            'mqttTlsClientKey',
            # Variantes défensives pour autres versions jMQTT
            'mqttuser',
            'mqttlogin',
            'broker_user',
            'login',
            'user',
            'username',
        }
    ),
    # Plugins à identifiant de compte, relevés à l'audit B3 (2026-09-08). Ces clés
    # ne peuvent pas entrer dans la regex globale : `username`/`login` masqués partout
    # casseraient l'affichage légitime de noms d'utilisateur. D'où le mécanisme 3.
    'cozytouch': frozenset({'username', 'login', 'user'}),
    'CozyTouch': frozenset({'username', 'login', 'user'}),
    'geotrav': frozenset({'username', 'login'}),
    'mail': frozenset({'username', 'smtp::username', 'smtp::login'}),
    'openvpn': frozenset({'username', 'login'}),
    'SomfyUnified': frozenset({'username', 'login'}),
    'calendar': frozenset(),  # Agenda (eqType_name réel : 'calendar')
    'alarm': frozenset(),  # Alarme (eqType_name réel : 'alarm') — pas de credentials dans blob
    'Thermostat': frozenset(),
    'thermostat': frozenset(),
    'JeedomConnect': frozenset(  # eqType_name réel : 'JeedomConnect' (sans espace)
        {
            'install_code',
            'pairing_code',
            'device_code',
            'access_code',
            'installCode',
        }
    ),
    'Script': frozenset(),
    'mqtt2': frozenset(),  # MQTT Manager (eqType_name réel : 'mqtt2') — pas de credentials
    'virtual': frozenset(),  # Virtuel (eqType_name réel : 'virtual')
    # Plugins top-10 initiaux (D15.2 J1-1)
    'Aqara': frozenset({'app_id', 'region_key', 'region'}),
    'Zigbee2MQTT': frozenset({'broker_user', 'login', 'user', 'username'}),
    'Sonos': frozenset(),
    'Philips Hue': frozenset({'username', 'bridge_user', 'bridge_username'}),
    'Z-Wave': frozenset(),
    'Netatmo': frozenset({'client_id', 'app_id'}),
    'ecodevices': frozenset({'login', 'user', 'username'}),
    'rfxcom': frozenset(),
}


def is_sensitive_key(
    key: str,
    plugin: str | None = None,
    *,
    segment_words: bool = True,
) -> bool:
    """True si la clé doit être masquée (regex mech 2, mots mech 2bis, extras mech 3).

    `segment_words=False` désactive le mécanisme 2bis. Réservé aux **noms de colonnes
    SQL**, qui viennent du schéma Jeedom — un ensemble fermé et connu. `dataStore.key`
    y est le NOM d'une variable, pas un secret : le segmenter masquerait la donnée
    même que l'outil doit rendre. Le 2bis vise les clés de CONTENU (champs JSON,
    clés de `config` définies par les plugins), où `keyGMG` peut exister.
    Défaut `True` : tout nouvel appelant reçoit le contrôle le plus fort.
    """
    if _BLOB_KEY_RE.search(key):
        return True
    if segment_words:
        if key.strip().lower() in _SECRET_EXACT_KEYS:
            return True
        if _key_words(key) & _SECRET_WORDS:
            return True
    if plugin:
        extras = _PLUGIN_EXTRA_KEYS.get(plugin, frozenset())
        if key in extras:
            return True
    return False


def sanitize_json_blob(
    blob: str | dict[str, Any] | None,
    plugin: str | None = None,
) -> tuple[dict[str, Any] | str | None, list[str]]:
    """Parse et sanitise un blob JSON (colonne configuration/options).

    Retourne (blob_sanitisé, clés_filtrées).
    - None → (None, [])
    - Chaîne vide → ({}, [])
    - JSON invalide → (chaîne originale, [])
    - JSON non-dict (array, scalar) → (valeur parsée, [])
    - Dict → filtrage récursif des clés sensibles
    """
    if blob is None:
        return None, []

    if isinstance(blob, str):
        blob = blob.strip()
        if not blob:
            return {}, []
        try:
            data: Any = json.loads(blob)
        except (json.JSONDecodeError, ValueError):
            return blob, []
    else:
        data = blob

    if not isinstance(data, dict):
        return data, []

    result: dict[str, Any] = {}
    filtered: list[str] = []

    for key, value in data.items():
        if is_sensitive_key(key, plugin):
            result[key] = FILTERED
            filtered.append(key)
        elif isinstance(value, dict):
            nested, nested_filtered = sanitize_json_blob(value, plugin)
            result[key] = nested
            filtered.extend(f'{key}.{f}' for f in nested_filtered)
        else:
            result[key] = value

    return result, filtered


def _sanitize_config_row(
    row: dict[str, Any],
    plugin: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Cas spécial table config : mask value si key est sensible (D15.1).

    La colonne key reste visible (transparence LLM-side).

    Le `plugin` vient de la row elle-même (colonne `plugin`, whitelistée mech 1) :
    aucun appelant ne peut l'oublier. L'argument explicite reste prioritaire.
    Sans lui, le mécanisme 3 était INERTE sur cette table — or c'est là que vivent
    les identifiants de compte des plugins (trou trouvé à l'audit B3, 2026-09-08).
    """
    key_name = str(row.get('key', ''))
    row_plugin = plugin or row.get('plugin') or None
    if is_sensitive_key(key_name, row_plugin):
        return {**row, 'value': FILTERED}, [key_name]
    return dict(row), []


def sanitize_row(
    row: dict[str, Any],
    table: str | None = None,
    plugin: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Applique les 3 mécanismes de sanitisation sur une row.

    Retourne (row_sanitisée, champs_filtrés).

    Ordre d'application :
    1. Whitelist par table (mech 1) — champ absent → masqué
    2. Blob columns → sanitize_json_blob (mech 2+3)
    3. Regex sur nom de champ (mech 2, défense en profondeur)
    """
    if table == 'config':
        return _sanitize_config_row(row, plugin)

    whitelist = _TABLE_WHITELISTS.get(table) if table else None
    result: dict[str, Any] = {}
    filtered: list[str] = []

    for key, value in row.items():
        # Mech 1 : whitelist
        if whitelist is not None and key not in whitelist:
            result[key] = FILTERED
            filtered.append(key)
            continue

        # Mech 2+3 : blob columns → parse et filtre le JSON interne
        if key in _BLOB_COLUMNS:
            sanitized_blob, blob_filtered = sanitize_json_blob(value, plugin)
            result[key] = sanitized_blob
            filtered.extend(f'{key}.{f}' for f in blob_filtered)
            continue

        # Mech 2 : regex sur le nom de la COLONNE (défense en profondeur).
        # 2bis désactivé : les noms de colonnes viennent du schéma Jeedom, fermé et
        # connu — et `dataStore.key` est le nom d'une variable, pas un secret.
        if is_sensitive_key(key, plugin, segment_words=False):
            result[key] = FILTERED
            filtered.append(key)
            continue

        result[key] = value

    return result, filtered


def sanitize_rows(
    rows: list[dict[str, Any]],
    table: str | None = None,
    plugin: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Sanitise une liste de rows.

    Retourne (rows_sanitisées, champs_filtrés_distincts_triés).
    """
    sanitized: list[dict[str, Any]] = []
    all_filtered: set[str] = set()

    for row in rows:
        san_row, row_filtered = sanitize_row(row, table, plugin)
        sanitized.append(san_row)
        all_filtered.update(row_filtered)

    return sanitized, sorted(all_filtered)


def wrap_result(
    data: list[dict[str, Any]] | dict[str, Any],
    filtered_fields: list[str],
) -> dict[str, Any]:
    """Enveloppe les données sanitisées pour la réponse MCP.

    Ajoute _filtered_fields pour transparence LLM-side (D15.1).
    """
    if isinstance(data, list):
        return {'rows': data, '_filtered_fields': filtered_fields}
    return {**data, '_filtered_fields': filtered_fields}
