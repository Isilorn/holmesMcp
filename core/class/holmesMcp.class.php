<?php
/* This file is part of Holmes MCP.
 * Licence : AGPL-3.0 — see LICENSE
 */

class holmesMcp extends eqLogic {

    // ── Daemon lifecycle ──────────────────────────────────────────────────────

    public static function deamon_info() {
        $return = [
            'log'       => __CLASS__,
            'state'     => 'nok',
            'launchable' => 'ok',
        ];
        $pid_file = jeedom::getTmpFolder(__CLASS__) . '/daemon.pid';
        if (file_exists($pid_file)) {
            $pid = trim(file_get_contents($pid_file));
            if ($pid !== '' && file_exists('/proc/' . $pid)) {
                $return['state'] = 'ok';
                $return['pid']   = $pid;
            }
        }
        if (!self::_isPythonReady()) {
            $return['launchable'] = 'nok';
            $return['launchable_message'] = __('Dépendances Python non installées', __FILE__);
        }
        return $return;
    }

    public static function deamon_start($_params = []) {
        self::deamon_stop();
        $deamon_info = self::deamon_info();
        if ($deamon_info['launchable'] !== 'ok') {
            throw new Exception(__('Dépendances Python manquantes — installez les dépendances d\'abord', __FILE__));
        }
        $daemon_path = realpath(__DIR__ . '/../../resources/holmesMcpd');
        $log_path    = log::getPathToLog(__CLASS__);
        $tmp_folder  = jeedom::getTmpFolder(__CLASS__);
        $pid_file    = $tmp_folder . '/daemon.pid';
        $port        = intval(config::byKey('port', __CLASS__, 8765));

        $cmd  = system::getCmdPython3(__CLASS__);
        $cmd .= ' ' . $daemon_path . '/holmesMcpd.py';
        $cmd .= ' --loglevel '   . log::convertLogLevel(log::getLogLevel(__CLASS__));
        $cmd .= ' --socketport ' . config::byKey('socketport', __CLASS__, 55000);
        $cmd .= ' --apikey '        . jeedom::getApiKey(__CLASS__);
        $cmd .= ' --jeedom-apikey ' . jeedom::getApiKey();
        $cmd .= ' --port '          . $port;
        $cmd .= ' --pid '        . $pid_file;
        $cmd .= ' --callback '   . network::getNetworkAccess('internal', 'http:127.0.0.1:port:comp') . '/core/php/jeeholmesMcp.php';

        log::add(__CLASS__, 'debug', 'Démarrage daemon : ' . $cmd);
        exec($cmd . ' >> ' . $log_path . ' 2>&1 &');

        $i = 0;
        while ($i < 20) {
            $info = self::deamon_info();
            if ($info['state'] === 'ok') {
                log::add(__CLASS__, 'info', 'Daemon démarré (PID ' . $info['pid'] . ', port ' . $port . ')');
                return;
            }
            sleep(1);
            $i++;
        }
        log::add(__CLASS__, 'error', 'Le daemon n\'a pas démarré dans les 20 secondes');
    }

    public static function deamon_stop() {
        $pid_file = jeedom::getTmpFolder(__CLASS__) . '/daemon.pid';
        if (file_exists($pid_file)) {
            $pid = trim(file_get_contents($pid_file));
            if ($pid !== '') {
                system('kill ' . intval($pid) . ' 2>/dev/null');
                usleep(500000);
            }
            unlink($pid_file);
        }
        exec("pkill -f 'holmesMcpd.py' 2>/dev/null");
    }

    // ── Dependency management ─────────────────────────────────────────────────

    public static function dependancy_info() {
        $return = [
            'log'           => __CLASS__ . '_update',
            'progress_file' => jeedom::getTmpFolder(__CLASS__) . '/dependency',
            'state'         => 'ok',
        ];
        if (file_exists($return['progress_file'])) {
            $return['state'] = 'in_progress';
            return $return;
        }
        if (!self::_isPythonReady()) {
            $return['state'] = 'nok';
        }
        return $return;
    }

    public static function dependancy_install() {
        log::add(__CLASS__, 'info', 'Installation des dépendances...');
        $return = [
            'log'           => __CLASS__ . '_update',
            'progress_file' => jeedom::getTmpFolder(__CLASS__) . '/dependency',
        ];
        system::update(__CLASS__);
        return $return;
    }

    // ── Config helpers ────────────────────────────────────────────────────────

    public static function getPort() {
        return intval(config::byKey('port', __CLASS__, 8765));
    }

    public static function getMcpUrl() {
        $ip   = config::byKey('internalAddr', 'core', '127.0.0.1');
        $port = self::getPort();
        return 'http://' . $ip . ':' . $port . '/mcp';
    }

    // ── Token management ──────────────────────────────────────────────────────

    public static function getTokenForUser($user_id) {
        return config::byKey('token_' . $user_id, __CLASS__, '');
    }

    public static function generateTokenForUser($user_id) {
        $token = bin2hex(random_bytes(32));
        config::save('token_' . $user_id, $token, __CLASS__);
        return $token;
    }

    // ── Activity log ─────────────────────────────────────────────────────────

    /**
     * Retourne les événements tool_call du log daemon (JSON Lines structlog).
     *
     * @param int   $limit   Nombre max d'entrées retournées
     * @param array $filters Clés optionnelles : user, tool, status, since (timestamp Unix)
     */
    public static function getActivityLogs($limit = 200, $filters = []) {
        $log_path = log::getPathToLog(__CLASS__);
        if (!file_exists($log_path) || !is_readable($log_path)) {
            return [];
        }
        $lines = @file($log_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if (!$lines) {
            return [];
        }
        $entries = [];
        foreach (array_reverse($lines) as $line) {
            $data = json_decode(trim($line), true);
            if (!is_array($data) || ($data['event'] ?? '') !== 'tool_call') {
                continue;
            }
            if (!empty($filters['user']) && ($data['user'] ?? '') !== $filters['user']) {
                continue;
            }
            if (!empty($filters['tool']) && ($data['tool'] ?? '') !== $filters['tool']) {
                continue;
            }
            if (!empty($filters['status']) && ($data['status'] ?? '') !== $filters['status']) {
                continue;
            }
            if (!empty($filters['since'])) {
                $ts = strtotime($data['timestamp'] ?? '');
                if ($ts === false || $ts < (int)$filters['since']) {
                    continue;
                }
            }
            $entries[] = [
                'timestamp'      => $data['timestamp']      ?? '',
                'user'           => $data['user']           ?? '?',
                'tool'           => $data['tool']           ?? '?',
                'params_summary' => $data['params_summary'] ?? '',
                'duration_ms'    => (int)($data['duration_ms'] ?? 0),
                'status'         => $data['status']         ?? 'ok',
                'error'          => $data['error']          ?? null,
            ];
            if (count($entries) >= $limit) {
                break;
            }
        }
        return $entries;
    }

    // ── Internal helpers ──────────────────────────────────────────────────────

    private static function _isPythonReady() {
        $venv_python = __DIR__ . '/../../resources/python_venv/bin/python3';
        if (file_exists($venv_python)) {
            $result = shell_exec($venv_python . ' -c "import mcp" 2>&1');
            return ($result === null || trim($result) === '');
        }
        return false;
    }

    // ── eqLogic overrides (optionnels V1) ─────────────────────────────────────

    public function postSave() {
    }

    public function preRemove() {
    }
}
