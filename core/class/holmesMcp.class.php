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
        $cmd .= ' --apikey '     . jeedom::getApiKey(__CLASS__);
        $cmd .= ' --port '       . $port;
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

    // ── Internal helpers ──────────────────────────────────────────────────────

    private static function _isPythonReady() {
        $venv_python = realpath(__DIR__ . '/../../resources/venv/bin/python3');
        if ($venv_python && file_exists($venv_python)) {
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
