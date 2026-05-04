<?php
/* This file is part of Holmes MCP. Licence : AGPL-3.0 — see LICENSE */

try {
    require_once dirname(__FILE__) . '/../../../../core/php/core.inc.php';
    include_file('core', 'authentification', 'php');

    if (!isConnect('admin')) {
        throw new Exception(__('Accès non autorisé', __FILE__));
    }

    $action = init('action');

    if ($action === 'getMcpUrl') {
        ajax::success(holmesMcp::getMcpUrl());
    }

    if ($action === 'generateToken') {
        $user_id = init('user_id');
        if (empty($user_id)) {
            throw new Exception(__('user_id manquant', __FILE__));
        }
        ajax::success(holmesMcp::generateTokenForUser($user_id));
    }

    if ($action === 'getToken') {
        $user_id = init('user_id');
        ajax::success(holmesMcp::getTokenForUser($user_id));
    }

    if ($action === 'getLogs') {
        $filters = [];
        $user   = init('user',   '');
        $tool   = init('tool',   '');
        $status = init('status', '');
        $window = intval(init('window', 86400));
        if ($user   !== '') { $filters['user']   = $user; }
        if ($tool   !== '') { $filters['tool']   = $tool; }
        if ($status !== '') { $filters['status'] = $status; }
        if ($window  >  0)  { $filters['since']  = time() - $window; }
        ajax::success(holmesMcp::getActivityLogs(200, $filters));
    }

    throw new Exception(__('Action non reconnue : ' . $action, __FILE__));
} catch (Exception $e) {
    ajax::error(displayException($e), $e->getCode());
}
