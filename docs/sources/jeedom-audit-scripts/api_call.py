#!/usr/bin/env python3
"""Wrapper JSON-RPC Jeedom — lecture seule, blacklist V1, retry, filtrage sensible.

Entrée (stdin) : {"method": "scenario::byId", "params": {"id": 70}}
Sortie (stdout): {"result": {...}, "_filtered_fields": [...]}

Usage :
    echo '{"method": "ping"}' | python3 scripts/api_call.py
    echo '{"method": "scenario::byId", "params": {"id": 70}}' | python3 scripts/api_call.py
"""

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import credentials as _creds
from _common import sensitive_fields as _sf

# Méthodes explicitement blacklistées V1 (D3.4).
_BLACKLIST_EXACT: frozenset[str] = frozenset([
    "cmd::execCmd",
    "scenario::changeState",
    "datastore::save",
    "interact::tryToReply",
])

# Verbes qui signalent une écriture — bloqués partout dans le nom de méthode.
_BLACKLIST_VERB_RE = re.compile(
    r"::(save|exec|delete|remove|update|set|add|create|send|apply|move|copy|import|export)\b",
    re.IGNORECASE,
)

_JEEDOM_API_PATH = "/core/api/jeeApi.php"


def is_blacklisted(method: str) -> bool:
    return method in _BLACKLIST_EXACT or bool(_BLACKLIST_VERB_RE.search(method))


def _build_ssl_context(verify: bool) -> ssl.SSLContext:
    if verify:
        return ssl.create_default_context()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _call_api(
    api_url: str,
    api_key: str,
    method: str,
    params: dict,
    timeout: int = 15,
    verify_ssl: bool = True,
) -> dict:
    """Effectue un appel JSON-RPC et retourne le dict brut de la réponse."""
    endpoint = api_url.rstrip("/") + _JEEDOM_API_PATH
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": {"apikey": api_key, **params},
        "id": 1,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    ctx = _build_ssl_context(verify_ssl)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return {"_transport_error": f"HTTP {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"_transport_error": str(exc.reason)}
    except TimeoutError:
        return {"_transport_error": f"Timeout ({timeout}s)"}
    except json.JSONDecodeError as exc:
        return {"_transport_error": f"Réponse non-JSON : {exc}"}


def run(
    method: str,
    params: dict | None = None,
    creds: dict | None = None,
    timeout: int = 15,
) -> dict:
    """Appel JSON-RPC avec blacklist, retry sur timeout, filtrage sensible.

    Returns dict with keys: result, _filtered_fields (success) or error, code (failure).
    """
    if creds is None:
        creds = _creds.load()

    if is_blacklisted(method):
        return {
            "error": f"Méthode blacklistée V1 (lecture seule) : {method!r}",
            "code": "api::forbidden::method",
        }

    api_url = creds.get("api_url", "").strip()
    api_key = creds.get("api_key", "").strip()

    if not api_url or not api_key:
        return {
            "error": (
                "api_url ou api_key non configurés — lancez : python3 scripts/setup.py"
            )
        }

    verify_ssl = creds.get("verify_ssl", True)
    _params = params or {}

    response = _call_api(api_url, api_key, method, _params, timeout=timeout, verify_ssl=verify_ssl)

    # Retry unique sur erreur réseau/timeout (pas sur erreur JSON-RPC).
    if "_transport_error" in response:
        response = _call_api(api_url, api_key, method, _params, timeout=timeout, verify_ssl=verify_ssl)

    if "_transport_error" in response:
        return {"error": response["_transport_error"]}

    # Erreur JSON-RPC standard : {"jsonrpc":"2.0","error":{"code":...,"message":...},"id":1}
    if "error" in response:
        rpc_error = response["error"]
        if isinstance(rpc_error, dict):
            return {
                "error": rpc_error.get("message", "Erreur JSON-RPC inconnue"),
                "code": rpc_error.get("code"),
            }
        return {"error": str(rpc_error)}

    result = response.get("result")

    if isinstance(result, dict):
        filtered, redacted = _sf.filter_row(result)
        return {"result": filtered, "_filtered_fields": redacted}

    if isinstance(result, list):
        filtered_rows, redacted = _sf.filter_rows(result)
        return {"result": filtered_rows, "_filtered_fields": redacted}

    # Résultat scalaire (ex. ping → "ok", version → "4.5.3")
    return {"result": result, "_filtered_fields": []}


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

    method = payload.get("method", "").strip()
    if not method:
        print(json.dumps({"error": "Clé 'method' manquante ou vide"}))
        sys.exit(1)

    params = payload.get("params") or {}
    result = run(method, params=params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
