#!/usr/bin/env python3
"""Wrapper SQL générique pour jeedom-audit.

Entrée (stdin) : {"query": "SELECT ...", "params": [...]}
Sortie (stdout): {"rows": [...], "_filtered_fields": [...]}

Usage :
    echo '{"query": "SELECT id, name FROM eqLogic LIMIT 5"}' | python3 scripts/db_query.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import credentials as _creds
from _common import ssh as _ssh
from _common import sensitive_fields as _sf

# Mots réservés MySQL/MariaDB présents comme noms de colonnes/tables dans Jeedom :
# `trigger` dans scenario.trigger, `repeat` dans calendar_event.repeat,
# `update` comme nom de table (table des versions plugins/core).
_RESERVED_RE = re.compile(r"\b(trigger|repeat|update)\b", re.IGNORECASE)


def _escape_trigger(query: str) -> str:
    """Ajoute des backticks autour des mots réservés MySQL/MariaDB si absent."""
    def replacer(m: re.Match) -> str:
        start = m.start()
        # Déjà entre backticks ?
        if start > 0 and query[start - 1] == "`":
            return m.group()
        return f"`{m.group()}`"

    return _RESERVED_RE.sub(replacer, query)


def _substitute_params(query: str, params: list) -> str:
    """Substitution positionnelle des paramètres (? → valeur échappée).

    Uniquement pour des valeurs scalaires — pas d'injection possible
    car les valeurs sont encadrées par des guillemets simples échappés.
    """
    result = []
    param_iter = iter(params)
    for char in query:
        if char == "?":
            value = next(param_iter)
            if value is None:
                result.append("NULL")
            elif isinstance(value, bool):
                result.append("1" if value else "0")
            elif isinstance(value, (int, float)):
                result.append(str(value))
            else:
                escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
                result.append(f"'{escaped}'")
        else:
            result.append(char)
    return "".join(result)


def run(query: str, params: list | None = None, creds: dict | None = None) -> dict:
    """Exécute la requête et retourne {"rows": [...], "_filtered_fields": [...]}."""
    if creds is None:
        creds = _creds.load()

    if params:
        query = _substitute_params(query, params)

    query = _escape_trigger(query)

    result = _ssh.mysql_json(
        alias=creds["ssh_alias"],
        db=creds["db_name"],
        query=query,
    )

    if not result.ok:
        return {
            "error": result.stderr or f"mysql exited with code {result.returncode}",
            "rows": [],
            "_filtered_fields": [],
        }

    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "error": f"Impossible de parser la sortie MySQL : {exc}",
            "raw": result.stdout[:500],
            "rows": [],
            "_filtered_fields": [],
        }

    filtered_rows, redacted = _sf.filter_rows(rows)
    return {"rows": filtered_rows, "_filtered_fields": redacted}


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "Entrée vide — fournir JSON sur stdin"}))
        sys.exit(1)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"JSON invalide : {exc}"}))
        sys.exit(1)

    query = payload.get("query", "").strip()
    if not query:
        print(json.dumps({"error": "Clé 'query' manquante ou vide"}))
        sys.exit(1)

    params = payload.get("params", [])
    result = run(query, params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
