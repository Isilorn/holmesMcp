"""Lecture des fichiers de log Jeedom (D4bis.6).

Dérivé de jeedom-audit/logs_query.py — lecture locale directe au lieu de SSH.
Ref jeedom-audit : logs_query.py @ commit à préciser en J1-2 (D7.4).
"""

from __future__ import annotations

import re
from pathlib import Path

import structlog

log = structlog.get_logger('holmesMcp.logs')

# Chemins candidats pour les logs Jeedom, par ordre de priorité.
_LOG_DIRS = [
    Path('/var/www/html/log'),
    Path('/usr/share/nginx/www/jeedom/log'),
]

DEFAULT_LINES = 100

# Accepte un nom simple ou un chemin en un seul niveau de sous-répertoire.
# Exemples valides : "core", "scenarioLog/scenario70.log", "jMQTT"
_LOG_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+(/[a-zA-Z0-9_.-]+)?$')


def validate_log_name(name: str) -> None:
    """Lève ValueError si le nom de log ne respecte pas la convention."""
    if not _LOG_NAME_RE.match(name):
        raise ValueError(
            f'Nom de log invalide : {name!r} — '
            'alphanumérique + tiret/underscore, un seul sous-répertoire autorisé'
        )


def resolve_log_path(log_name: str, log_dirs: list[Path] | None = None) -> Path | None:
    """Retourne le premier chemin absolu valide du log, ou None."""
    dirs = log_dirs if log_dirs is not None else _LOG_DIRS
    for log_dir in dirs:
        candidate = log_dir / log_name
        if candidate.is_file():
            return candidate
    return None


def tail(
    log_name: str,
    lines: int = DEFAULT_LINES,
    grep: str | None = None,
    log_dirs: list[Path] | None = None,
) -> dict:
    """Retourne les N dernières lignes d'un log Jeedom.

    Retourne {'log_file': ..., 'lines': [...], 'count': N}.
    Retourne {'error': ..., 'log_file': None, 'lines': [], 'count': 0} en échec.
    """
    try:
        validate_log_name(log_name)
    except ValueError as exc:
        return {'error': str(exc), 'log_file': None, 'lines': [], 'count': 0}

    log_path = resolve_log_path(log_name, log_dirs)
    if log_path is None:
        return {
            'error': f'Fichier log introuvable : {log_name!r}',
            'log_file': None,
            'lines': [],
            'count': 0,
        }

    try:
        all_lines = log_path.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError as exc:
        return {
            'error': str(exc),
            'log_file': str(log_path),
            'lines': [],
            'count': 0,
        }

    all_lines = all_lines[-lines:]

    if grep:
        pattern = re.compile(re.escape(grep), re.IGNORECASE)
        all_lines = [line for line in all_lines if pattern.search(line)]

    log.debug('logs_tail_ok', log_file=str(log_path), count=len(all_lines))
    return {
        'log_file': str(log_path),
        'lines': all_lines,
        'count': len(all_lines),
    }
