#!/usr/bin/env python3
"""Résolution batch de #ID# → #[Objet][Équipement][Commande]# dans du texte.

Entrée (stdin) : {"text": "... #15663# ... #15669# ..."}
Sortie (stdout): {
    "resolved": "... #[Maison][Présence Géraud][BLE présent]# ...",
    "mapping": {"15663": "[Maison][Présence Géraud][BLE présent]", ...},
    "unresolved": [99999]
}

Usage :
    echo '{"text": "Si #15663# == 1 alors #15670#"}' | python3 scripts/resolve_cmd_refs.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import credentials as _creds

_ID_PATTERN = re.compile(r"#(\d+)#")

# Cache de session : {cmd_id_int → "[Objet][Équipement][Commande]"}
_SESSION_CACHE: dict[int, str] = {}

_RESOLVE_SQL = (
    "SELECT c.id, COALESCE(o.name, '') AS objet, e.name AS equipement, c.name AS commande"
    " FROM cmd c"
    " JOIN eqLogic e ON c.eqLogic_id = e.id"
    " LEFT JOIN object o ON e.object_id = o.id"
    " WHERE c.id IN ({placeholders})"
)


def _fetch_names(ids: list[int], creds: dict) -> dict[int, str]:
    """Requête SQL batch → {cmd_id: '[O][E][C]'}."""
    if not ids:
        return {}

    import db_query as _dq

    query = _RESOLVE_SQL.format(placeholders=", ".join(str(i) for i in ids))
    result = _dq.run(query, creds=creds)

    mapping: dict[int, str] = {}
    for row in result.get("rows", []):
        cmd_id = int(row["id"])
        label = f"[{row.get('objet') or ''}][{row.get('equipement') or ''}][{row.get('commande') or ''}]"
        mapping[cmd_id] = label
    return mapping


def resolve(text: str, creds: dict | None = None) -> dict:
    """Résout tous les #ID# numériques dans *text*.

    Retourne :
        resolved   : texte avec #ID# remplacés par #[O][E][C]# ou #ID_NON_RÉSOLU:X#
        mapping    : {str(id): "[O][E][C]"} pour les IDs résolus
        unresolved : IDs absents de la DB (liste triée)
    """
    if creds is None:
        creds = _creds.load()

    ids_found = {int(m.group(1)) for m in _ID_PATTERN.finditer(text)}
    to_fetch = [i for i in ids_found if i not in _SESSION_CACHE]

    if to_fetch:
        _SESSION_CACHE.update(_fetch_names(to_fetch, creds))

    mapping: dict[str, str] = {}
    unresolved: list[int] = []
    for cmd_id in ids_found:
        if cmd_id in _SESSION_CACHE:
            mapping[str(cmd_id)] = _SESSION_CACHE[cmd_id]
        else:
            unresolved.append(cmd_id)

    def _replacer(m: re.Match) -> str:
        cmd_id = int(m.group(1))
        if cmd_id in _SESSION_CACHE:
            return f"#{_SESSION_CACHE[cmd_id]}#"
        return f"#ID_NON_RÉSOLU:{cmd_id}#"

    return {
        "resolved": _ID_PATTERN.sub(_replacer, text),
        "mapping": mapping,
        "unresolved": sorted(unresolved),
    }


def clear_cache() -> None:
    """Vide le cache de session (utile entre deux requêtes indépendantes)."""
    _SESSION_CACHE.clear()


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

    text = payload.get("text", "")
    if not isinstance(text, str):
        print(json.dumps({"error": "Clé 'text' manquante ou non-string"}))
        sys.exit(1)

    result = resolve(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
