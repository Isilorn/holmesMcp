<?php
/* This file is part of Holmes MCP. Licence : AGPL-3.0 — see LICENSE */
/* Callback entrant : daemon Holmes MCP → Jeedom core
 * Pattern : doc.jeedom.com/fr_FR/dev/daemon_plugin#_communication
 */

require_once dirname(__FILE__) . '/../../../../core/php/core.inc.php';

$apikey = init('apikey');
if (!jeedom::apiAccess($apikey, 'holmesMcp')) {
    log::add('holmesMcp', 'error', 'Accès callback refusé — apikey invalide');
    http_response_code(403);
    die('Access denied');
}

$type = init('type');
$data = json_decode(file_get_contents('php://input'), true) ?? [];

log::add('holmesMcp', 'debug', 'Callback reçu type=' . $type . ' data=' . json_encode($data));

switch ($type) {
    case 'heartbeat':
        // Le daemon envoie un heartbeat périodique — rien à traiter côté PHP
        break;

    default:
        log::add('holmesMcp', 'warning', 'Callback type inconnu : ' . $type);
        break;
}

http_response_code(200);
echo json_encode(['result' => 'ok']);
