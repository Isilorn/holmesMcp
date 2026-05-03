#!/usr/bin/env python3
"""Tail structuré des logs Jeedom via SSH.

Entrée (stdin) : {"log": "core", "lines": 100, "grep": "ERROR"}
Sortie (stdout): {"log_file": "...", "lines": [...], "count": N}

Usage :
    echo '{"log": "core", "lines": 50}' | python3 scripts/logs_query.py
    echo '{"log": "jMQTT", "lines": 100, "grep": "ERROR"}' | python3 scripts/logs_query.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import credentials as _creds
from _common import ssh as _ssh

# Chemins candidats pour les logs Jeedom, par ordre de priorité.
_LOG_DIRS = [
    "/var/www/html/log",
    "/usr/share/nginx/www/jeedom/log",
]

DEFAULT_LINES = 100

# Accepte un nom simple ou un chemin en un seul niveau de sous-répertoire.
# Exemples valides : "core", "scenarioLog/scenario70.log", "jMQTT"
_LOG_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+(/[a-zA-Z0-9_.-]+)?$")


def _validate_log_name(name: str) -> None:
    if not _LOG_NAME_RE.match(name):
        raise ValueError(
            f"Nom de log invalide : {name!r} — "
            "alphanumérique + tiret/underscore, un seul sous-répertoire autorisé"
        )


def _resolve_log_path(alias: str, log_name: str) -> str | None:
    """Retourne le premier chemin absolu valide du log sur la box, ou None."""
    # log_name est déjà validé par _validate_log_name — interpolation sûre.
    candidates = " ".join(f"{d}/{log_name}" for d in _LOG_DIRS)
    cmd = f'for f in {candidates}; do [ -f "$f" ] && echo "$f" && break; done'
    result = _ssh.run(alias, cmd)
    if result.ok:
        path = result.stdout.strip()
        if path:
            return path
    return None


def run(
    log_name: str,
    lines: int = DEFAULT_LINES,
    grep: str | None = None,
    creds: dict | None = None,
) -> dict:
    """Tail SSH d'un log Jeedom.

    Returns dict with keys: log_file, lines, count (and error on failure).
    """
    if creds is None:
        creds = _creds.load()

    try:
        _validate_log_name(log_name)
    except ValueError as exc:
        return {"error": str(exc), "log_file": None, "lines": [], "count": 0}

    alias = creds["ssh_alias"]

    log_file = _resolve_log_path(alias, log_name)
    if log_file is None:
        return {
            "error": (
                f"Fichier log introuvable : {log_name!r} "
                f"(chemins essayés : {_LOG_DIRS})"
            ),
            "log_file": None,
            "lines": [],
            "count": 0,
        }

    result = _ssh.run(alias, f"tail -n {int(lines)} {log_file}")
    if not result.ok:
        return {
            "error": result.stderr or f"tail a retourné le code {result.returncode}",
            "log_file": log_file,
            "lines": [],
            "count": 0,
        }

    all_lines = result.stdout.splitlines()

    # Filtrage grep côté client — évite l'injection shell via une valeur non contrôlée.
    if grep:
        pattern = re.compile(re.escape(grep), re.IGNORECASE)
        all_lines = [line for line in all_lines if pattern.search(line)]

    return {
        "log_file": log_file,
        "lines": all_lines,
        "count": len(all_lines),
    }


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

    log_name = payload.get("log", "").strip()
    if not log_name:
        print(json.dumps({"error": "Clé 'log' manquante ou vide"}))
        sys.exit(1)

    lines = int(payload.get("lines", DEFAULT_LINES))
    grep = payload.get("grep") or None

    try:
        result = run(log_name, lines=lines, grep=grep)
    except ValueError as exc:
        result = {"error": str(exc)}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
