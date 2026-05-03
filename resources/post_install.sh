#!/bin/bash
# Crée l'user MySQL jeedom_mcp_ro (lecture seule sur la base jeedom).
# Requiert root MySQL via unix_socket (disponible sur Bookworm via sudo mysql).

set -e

MCP_RO_USER="jeedom_mcp_ro"
MCP_RO_PASS=$(openssl rand -hex 16)
CONF_FILE="/etc/holmes_mcp_ro.conf"

# Génère le mot de passe une seule fois (idempotent)
if [ -f "$CONF_FILE" ]; then
    MCP_RO_PASS=$(grep '^password=' "$CONF_FILE" | cut -d= -f2)
else
    echo "password=${MCP_RO_PASS}" > "$CONF_FILE"
    chmod 640 "$CONF_FILE"
    chown root:www-data "$CONF_FILE"
fi

sudo mysql <<SQL
CREATE USER IF NOT EXISTS '${MCP_RO_USER}'@'localhost' IDENTIFIED BY '${MCP_RO_PASS}';
GRANT SELECT ON jeedom.* TO '${MCP_RO_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

if [ $? -eq 0 ]; then
    echo "[holmesMcp] user MySQL '${MCP_RO_USER}' prêt."
else
    echo "[holmesMcp] ERREUR : impossible de créer l'user MySQL. Vérifiez que sudo mysql est accessible." >&2
    exit 1
fi
