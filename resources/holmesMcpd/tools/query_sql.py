"""Famille 7 — Requête SQL libre (lecture seule).

Tool : query_sql.
Canal : MySQL RO — SELECT uniquement.
Sécurité : rejet non-SELECT (D5.6), blacklist tables sensibles, LIMIT injecté/plafonné,
           sanitisation runtime (D15.1), refus colonnes sensibles (D15.3).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import sqlparse
from _core import db as _db
from _domain.sanitize import sanitize_rows, wrap_result

if TYPE_CHECKING:
    import pymysql.connections

_SQL_DEFAULT_LIMIT = 50
_SQL_MAX_LIMIT = 200

# Tables interdites — données utilisateurs, sessions, credentials réseau
_BLACKLIST_TABLES: frozenset[str] = frozenset({'user', 'session', 'network'})

# Tables interdites — regex (nommages plugins avec credentials)
_BLACKLIST_TABLE_RE = re.compile(r'(?i)^(creds?|credentials?|password[s_]?\w*|token[s_]?\w*)$')

# D15.3 — colonnes sensibles interdites dans le SELECT
_SENSITIVE_COL_RE = re.compile(
    r'(?i)\b(password|passwd|pwd|token|apikey|api_key|secret|hash|'
    r'credentials?|private_key|access_key|client_secret|bearer)\b'
)

# Extraction des noms de tables depuis FROM / JOIN (backticks optionnels)
_TABLE_FROM_RE = re.compile(r'\bFROM\s+`?(\w+)`?', re.IGNORECASE)
_TABLE_JOIN_RE = re.compile(r'\bJOIN\s+`?(\w+)`?', re.IGNORECASE)

# Extraction du SELECT … FROM (pour vérification D15.3)
_SELECT_CLAUSE_RE = re.compile(r'SELECT\s+(.+?)\s+FROM\b', re.IGNORECASE | re.DOTALL)

# LIMIT dans la requête externe (pas dans une sous-requête — approximation V1)
_LIMIT_RE = re.compile(r'\bLIMIT\s+(\d+)\b', re.IGNORECASE)

# Auto-backtick — mots réservés MySQL courants dans le contexte Jeedom
_QUOTED_STR_RE = re.compile(r"'(?:[^'\\]|\\.)*'")
_RESERVED_BARE_RE = re.compile(
    r'(?<![`\w])\b(trigger|repeat|update)\b(?![`\w])',
    re.IGNORECASE,
)


def _check_select_only(sql: str) -> str | None:
    """Retourne None si OK, sinon un message d'erreur."""
    statements = [s for s in sqlparse.parse(sql.strip()) if s.value.strip()]
    if len(statements) != 1:
        return f'Une seule requête SELECT est autorisée — {len(statements)} statement(s) détecté(s)'
    stmt_type = statements[0].get_type()
    if stmt_type != 'SELECT':
        return f'Seules les requêtes SELECT sont autorisées — rejeté : {stmt_type or "inconnu"}'
    return None


def _extract_table_names(sql: str) -> list[str]:
    """Extrait tous les noms de tables référencés dans FROM et JOIN."""
    tables = [m.group(1).lower() for m in _TABLE_FROM_RE.finditer(sql)]
    tables += [m.group(1).lower() for m in _TABLE_JOIN_RE.finditer(sql)]
    return tables


def _check_blacklist(tables: list[str]) -> str | None:
    """Retourne None si OK, sinon un message d'erreur avec la table incriminée."""
    for table in tables:
        if table in _BLACKLIST_TABLES:
            return f"Table '{table}' interdite — données sensibles"
        if _BLACKLIST_TABLE_RE.match(table):
            return f"Table '{table}' interdite — pattern credentials détecté"
    return None


def _check_sensitive_columns(sql: str) -> str | None:
    """D15.3 — refuse si le SELECT liste explicitement des colonnes sensibles."""
    m = _SELECT_CLAUSE_RE.search(sql)
    if not m:
        return None
    cols_part = m.group(1)
    # SELECT * ne liste aucune colonne sensible explicitement — la sanitisation gère
    if cols_part.strip() == '*':
        return None
    if _SENSITIVE_COL_RE.search(cols_part):
        return 'Requête refusée — colonnes sensibles détectées dans SELECT (D15.3)'
    return None


def _auto_backtick_reserved(sql: str) -> str:
    """Backticks trigger/repeat/update comme identifiants, sans toucher aux littéraux 'string'."""
    parts: list[str] = []
    last = 0
    for m in _QUOTED_STR_RE.finditer(sql):
        parts.append(_RESERVED_BARE_RE.sub(r'`\1`', sql[last:m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_RESERVED_BARE_RE.sub(r'`\1`', sql[last:]))
    return ''.join(parts)


def _ensure_limit(sql: str) -> str:
    """Injecte LIMIT si absent, plafonne si supérieur à _SQL_MAX_LIMIT."""
    m = _LIMIT_RE.search(sql)
    if m:
        current = int(m.group(1))
        if current > _SQL_MAX_LIMIT:
            return _LIMIT_RE.sub(f'LIMIT {_SQL_MAX_LIMIT}', sql, count=1)
        return sql
    # Pas de LIMIT — l'ajouter (après suppression du ; final éventuel)
    sql_clean = sql.rstrip().rstrip(';').rstrip()
    return f'{sql_clean} LIMIT {_SQL_DEFAULT_LIMIT}'


def query_sql(
    conn: pymysql.connections.Connection,
    sql: str,
) -> dict[str, Any]:
    """Exécute une requête SELECT libre sur la base Jeedom (lecture seule).

    SÉCURITÉ
    --------
    - Seuls les SELECT sont acceptés (INSERT / UPDATE / DELETE / DROP → refusés).
    - Tables interdites : user, session, network, et tout nom ressemblant à
      "credentials", "password_store", "tokens", etc.
    - Colonnes sensibles interdites dans le SELECT : password, token, apikey,
      secret, private_key… (D15.3).
    - LIMIT injecté à 50 si absent ; plafonné à 200 même si spécifié plus grand.
    - Tous les résultats passent par la sanitisation runtime (D15.1) :
      champs sensibles remplacés par ***FILTERED***.

    TABLES UTILES JEEDOM
    --------------------
    - eqLogic       : équipements (id, name, eqType_name, object_id, isEnable)
    - cmd           : commandes (id, name, eqLogic_id, type, subType, currentValue)
    - scenario      : scénarios (id, name, isActive, mode) — lastLaunch/state via API seulement
    - object        : pièces/objets (id, name, father_id, isVisible)
    - dataStore     : variables persistantes (type, link_id, key, value)
    - config        : configuration (plugin, key, value — values sensibles filtrées)
    - history       : historique commandes (cmd_id, datetime, value)
    - historyArch   : historique archivé (cmd_id, datetime, value)
    - update        : plugins/mises à jour (logicalId, name, localVersion, remoteVersion, type)
                      WHERE type='plugin' = plugins installés (pas de table 'plugin')
    - message       : messages système (date, message, plugin, logicalId)
    - cron          : tâches planifiées (class, function, schedule, deamon, enable)

    MOTS RÉSERVÉS
    -------------
    Les colonnes `trigger`, `repeat`, `update` nécessitent des backticks :
    SELECT `trigger`, mode FROM scenario WHERE id = 42

    EXEMPLES
    --------
    - Tous les équipements d'un objet :
        SELECT id, name, eqType_name FROM eqLogic WHERE object_id = 3
    - Commandes historisées actives :
        SELECT id, name, currentValue FROM cmd WHERE isHistorized = 1 LIMIT 20
    - Dernières valeurs d'une commande :
        SELECT datetime, value FROM history WHERE cmd_id = 12 ORDER BY datetime DESC
    - Variables datastore d'un scénario :
        SELECT key, value FROM dataStore WHERE type = 'scenario' AND link_id = 5
    """
    sql = sql.strip()

    error = _check_select_only(sql)
    if error:
        return {'error': error, '_filtered_fields': []}

    tables = _extract_table_names(sql)

    error = _check_blacklist(tables)
    if error:
        return {'error': error, '_filtered_fields': []}

    error = _check_sensitive_columns(sql)
    if error:
        return {'error': error, '_filtered_fields': []}

    sql = _auto_backtick_reserved(sql)
    sql = _ensure_limit(sql)

    rows = _db.query(conn, sql)

    # Sanitisation avec la table principale si requête mono-table connue
    primary_table = tables[0] if len(tables) == 1 else None
    sanitized, filtered = sanitize_rows(rows, table=primary_table)

    return wrap_result(
        {'rows': sanitized, 'query': sql, 'count': len(sanitized)},
        filtered,
    )
