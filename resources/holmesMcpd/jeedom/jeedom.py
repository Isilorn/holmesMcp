"""Package Jeedom Python — helper de communication daemon↔Jeedom.

Adapté du template officiel Jeedom pour le plugin Holmes MCP.
Ref : doc.jeedom.com/fr_FR/dev/daemon_plugin
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
from collections.abc import Callable
from typing import Any

log = logging.getLogger('holmesMcp.jeedom')


class jeedom_utils:  # noqa: N801 — convention Jeedom
    """Utilitaires statiques."""

    @staticmethod
    def convert_log_level(level: str) -> int:
        mapping = {
            'debug':   logging.DEBUG,
            'info':    logging.INFO,
            'warning': logging.WARNING,
            'error':   logging.ERROR,
        }
        return mapping.get(level.lower(), logging.INFO)

    @staticmethod
    def pid_exists(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


class jeedom_com:  # noqa: N801 — convention Jeedom
    """Envoi de messages du daemon vers Jeedom (callback HTTP)."""

    def __init__(self, callback_url: str, apikey: str):
        self._url    = callback_url
        self._apikey = apikey

    def send_change_immediate(self, type_: str, data: dict[str, Any] = None) -> bool:
        """Envoie un message vers le callback Jeedom (jeeholmesMcp.php)."""
        if not self._url:
            return True
        try:
            import urllib.request
            payload = json.dumps({'type': type_, 'data': data or {}}).encode()
            url_with_key = self._url + '?apikey=' + self._apikey
            req = urllib.request.Request(
                url_with_key, data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
            return True
        except Exception as exc:
            log.debug('Erreur callback Jeedom : %s', exc)
            return False


class jeedom_socket:  # noqa: N801 — convention Jeedom
    """Socket TCP pour recevoir des commandes de Jeedom (PHP→daemon).

    Optionnel V1 — pattern Mips. Démarré uniquement si socketport > 0.
    """

    def __init__(self, port: int, callback: Callable[[dict], None]):
        self._port     = port
        self._callback = callback
        self._thread   = None
        self._running  = False

    def open(self) -> None:
        if self._port <= 0:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        log.debug('Socket Jeedom ouverte sur port %d', self._port)

    def close(self) -> None:
        self._running = False

    def _listen(self) -> None:
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(('127.0.0.1', self._port))
            srv.listen(5)
            srv.settimeout(1.0)
            while self._running:
                try:
                    conn, _ = srv.accept()
                    data = b''
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                    conn.close()
                    if data:
                        msg = json.loads(data.decode())
                        self._callback(msg)
                except TimeoutError:
                    pass
        except Exception as exc:
            log.error('Erreur socket Jeedom : %s', exc)
