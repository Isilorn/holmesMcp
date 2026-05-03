"""API JSON-RPC Jeedom localhost (D4bis.5-D4bis.7).

Dérivé de jeedom-audit/api_call.py — HTTP localhost au lieu de HTTP distant, sans SSL.
Ref jeedom-audit : api_call.py @ commit à préciser en J1-2 (D7.4).
Blacklist méthodes modifiantes (D5.1) intégrée.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

import structlog

log = structlog.get_logger('holmesMcp.api')

_JEEDOM_API_URL = 'http://127.0.0.1/core/api/jeeApi.php'

# Méthodes JSON-RPC explicitement blacklistées V1 (D5.1).
_BLACKLIST_EXACT: frozenset[str] = frozenset(
    [
        'cmd::execCmd',
        'scenario::changeState',
        'datastore::save',
        'interact::tryToReply',
    ]
)

# Verbes d'écriture bloqués sur tout nom de méthode.
_BLACKLIST_VERB_RE = re.compile(
    r'::(save|exec|delete|remove|update|set|add|create|send|apply|move|copy|import|export)\b',
    re.IGNORECASE,
)


def is_blacklisted(method: str) -> bool:
    return method in _BLACKLIST_EXACT or bool(_BLACKLIST_VERB_RE.search(method))


def call(
    apikey: str,
    method: str,
    params: dict | None = None,
    timeout: int = 15,
) -> dict:
    """Appel JSON-RPC en lecture seule avec blacklist et retry sur erreur réseau.

    Retourne {'result': ..., '_filtered_fields': []} en succès.
    Retourne {'error': ..., 'code': ...} en échec (blacklist, réseau, RPC).
    """
    if is_blacklisted(method):
        log.warning('api_blacklisted', method=method)
        return {
            'error': f'Méthode blacklistée V1 (lecture seule) : {method!r}',
            'code': 'api::forbidden::method',
        }

    response = _call_raw(apikey, method, params or {}, timeout)

    if '_transport_error' in response:
        log.warning('api_transport_retry', method=method, error=response['_transport_error'])
        response = _call_raw(apikey, method, params or {}, timeout)

    if '_transport_error' in response:
        return {'error': response['_transport_error']}

    if 'error' in response:
        rpc_err = response['error']
        if isinstance(rpc_err, dict):
            return {
                'error': rpc_err.get('message', 'Erreur JSON-RPC inconnue'),
                'code': rpc_err.get('code'),
            }
        return {'error': str(rpc_err)}

    result = response.get('result')
    log.debug('api_call_ok', method=method)
    return {'result': result, '_filtered_fields': []}


def _call_raw(apikey: str, method: str, params: dict, timeout: int) -> dict:
    payload = {
        'jsonrpc': '2.0',
        'method': method,
        'params': {'apikey': apikey, **params},
        'id': 1,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        _JEEDOM_API_URL,
        data=data,
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return {'_transport_error': f'HTTP {exc.code}: {exc.reason}'}
    except urllib.error.URLError as exc:
        return {'_transport_error': str(exc.reason)}
    except TimeoutError:
        return {'_transport_error': f'Timeout ({timeout}s)'}
    except json.JSONDecodeError as exc:
        return {'_transport_error': f'Réponse non-JSON : {exc}'}
