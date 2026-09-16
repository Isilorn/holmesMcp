"""Smoke test MCP propre — client officiel + asyncio.wait_for (pas de timeout OS).

Usage :
    sudo -u www-data python3 tests/smoke/smoke_mcp_clean.py http://127.0.0.1:8765/mcp <TOKEN>
"""

import asyncio
import sys

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def smoke(url: str, token: str) -> None:
    headers = {'Authorization': f'Bearer {token}'}
    async with streamablehttp_client(url, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as session:
            await asyncio.wait_for(session.initialize(), timeout=10.0)
            result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
            tools = sorted(t.name for t in result.tools)
            print(f'{len(tools)} tools: {tools}')
            assert len(tools) == 27, f'Attendu 27 tools, obtenu {len(tools)}'
    # Les deux `async with` sont sortis → FIN/ACK envoyés → pas de CLOSE-WAIT
    print('OK — connexion fermée proprement')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <url> <token>', file=sys.stderr)
        print('  ex: http://127.0.0.1:8765/mcp <TOKEN>', file=sys.stderr)
        sys.exit(1)
    asyncio.run(smoke(sys.argv[1], sys.argv[2]))
