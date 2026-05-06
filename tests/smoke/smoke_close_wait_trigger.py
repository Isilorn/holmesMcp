"""Reproduit le bug CLOSE-WAIT pour valider le watchdog.

Envoie un POST /mcp incomplet puis ferme le socket avec RST (SO_LINGER=0).
Le daemon doit détecter et loguer `close_wait_cleanup` dans les 30 s.

Usage :
    python3 tests/smoke/smoke_close_wait_trigger.py 8765 <TOKEN>
    # Attendre 15-30 s, puis vérifier :
    #   1. CPU daemon < 20%  →  ps aux | grep holmesMcpd | grep -v grep
    #   2. Log contient close_wait_cleanup
    #      sudo tail -50 /var/log/jeedom/holmesMcp.log | grep close_wait
"""

import socket
import sys
import time

HOST = '127.0.0.1'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ''

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# POST avec Content-Length annoncé mais body tronqué — uvicorn commence à lire
request = (
    f'POST /mcp HTTP/1.1\r\n'
    f'Host: {HOST}:{PORT}\r\n'
    f'Authorization: Bearer {TOKEN}\r\n'
    f'Content-Type: application/json\r\n'
    f'Content-Length: 200\r\n'
    f'\r\n'
    f'{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{'
    # body tronqué intentionnellement
)
s.sendall(request.encode())
time.sleep(0.5)

# RST = fermeture abrupte sans FIN → CLOSE-WAIT côté serveur garanti
s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x01\x00\x00\x00\x00\x00\x00\x00')
s.close()

print(f'Socket fermé avec RST sur {HOST}:{PORT}')
print('Attendre max 30 s, puis vérifier :')
print('  1. CPU daemon < 20%  →  ps aux | grep holmesMcpd | grep -v grep')
print('  2. Log daemon contient close_wait_cleanup')
print('     sudo tail -50 /var/log/jeedom/holmesMcp.log | grep close_wait')
