#!/usr/bin/env python3
"""Configuration initiale interactive de jeedom-audit."""

import json
import os
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

CREDENTIALS_PATH = Path.home() / ".config" / "jeedom-audit" / "credentials.json"

BANNER = """
╔══════════════════════════════════════════╗
║     jeedom-audit — Configuration        ║
╚══════════════════════════════════════════╝
"""


def _ask(prompt: str, default: str = "") -> str:
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    answer = input(display).strip()
    return answer if answer else default


def _ask_secret(prompt: str) -> str:
    import getpass
    return getpass.getpass(f"{prompt}: ").strip()


def _ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def _err(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)


def _section(title: str) -> None:
    print(f"\n── {title} ──")


# ── Étape 1 : SSH ──────────────────────────────────────────────────────────────

def setup_ssh() -> str:
    _section("Connexion SSH")
    alias = _ask("Alias SSH (défini dans ~/.ssh/config)", "Jeedom")
    result = subprocess.run(["ssh", alias, "echo ok"], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        _ok(f"SSH '{alias}' opérationnel")
    else:
        _err(f"SSH '{alias}' inaccessible : {result.stderr.strip()}")
        _err("Ajoutez l'alias dans ~/.ssh/config et relancez setup.py")
        sys.exit(1)
    return alias


# ── Étape 2 : MySQL ────────────────────────────────────────────────────────────

def _detect_jeedom_db(alias: str) -> dict:
    """Tente de lire la config DB depuis la box."""
    result = subprocess.run(
        ["ssh", alias, "grep -oP \"'(username|password|dbname)' => '\\K[^']+\" "
         "/var/www/html/core/config/common.config.php"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return {}
    lines = result.stdout.strip().splitlines()
    if len(lines) >= 3:
        return {"db_user_jeedom": lines[0], "db_password_jeedom": lines[1], "db_name": lines[2]}
    return {}


def setup_mysql(alias: str) -> dict:
    _section("MySQL read-only")

    db_name = _ask("Nom de la base de données", "jeedom")
    db_user = _ask("User MySQL read-only", "jeedom_audit_ro")

    # Vérifier si ~/.my.cnf existe côté serveur
    result = subprocess.run(
        ["ssh", alias, "test -f ~/.my.cnf && echo exists || echo missing"],
        capture_output=True, text=True, timeout=10,
    )
    mycnf_exists = "exists" in result.stdout

    if mycnf_exists:
        test = subprocess.run(
            ["ssh", alias, f"mysql {db_name} -e 'SELECT 1;' 2>&1"],
            capture_output=True, text=True, timeout=10,
        )
        if "1" in test.stdout:
            _ok("~/.my.cnf détecté et MySQL opérationnel")
            return {"db_name": db_name, "db_user": db_user, "db_password_source": "remote_mycnf"}

    # Pas de ~/.my.cnf — guider la création
    print(f"\n  ~/.my.cnf absent sur '{alias}'. Création guidée.")
    detected = _detect_jeedom_db(alias)

    print("\n  Pour créer le user read-only, exécutez sur la box :")
    print(f"    sudo mysql {db_name} -e \"")
    print(f"      CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '<mot-de-passe>';")
    print(f"      GRANT SELECT ON {db_name}.* TO '{db_user}'@'localhost';")
    print(f"      FLUSH PRIVILEGES;\"")

    ro_password = _ask_secret(f"\n  Mot de passe pour '{db_user}'@localhost (laissez vide si déjà créé)")

    if ro_password:
        # Créer ~/.my.cnf côté serveur
        mycnf_content = f"[client]\nuser={db_user}\npassword={ro_password}\nhost=localhost\n"
        write_result = subprocess.run(
            ["ssh", alias, f"printf '%s' '{mycnf_content}' > ~/.my.cnf && chmod 600 ~/.my.cnf"],
            capture_output=True, text=True, timeout=10,
        )
        if write_result.returncode == 0:
            _ok("~/.my.cnf créé (perm 600)")
        else:
            _err(f"Impossible de créer ~/.my.cnf : {write_result.stderr}")

    # Test final
    test = subprocess.run(
        ["ssh", alias, f"mysql {db_name} -e 'SELECT COUNT(*) FROM eqLogic;' 2>&1"],
        capture_output=True, text=True, timeout=10,
    )
    if test.returncode == 0:
        _ok(f"MySQL opérationnel ({test.stdout.strip()} eqLogics trouvés)")
    else:
        _err(f"MySQL inaccessible : {test.stderr.strip()}")
        _err("Vérifiez le user et relancez setup.py")
        sys.exit(1)

    return {"db_name": db_name, "db_user": db_user, "db_password_source": "remote_mycnf"}


# ── Étape 3 : API Jeedom ───────────────────────────────────────────────────────

def _detect_api_key(alias: str) -> str:
    result = subprocess.run(
        ["ssh", alias,
         "php -r \"define('ROOT','/var/www/html');"
         "require_once('/var/www/html/core/php/core.inc.php');"
         "echo config::byKey('api');\""],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return ""


def _detect_api_url(alias: str) -> str:
    result = subprocess.run(
        ["ssh", alias,
         "php -r \"define('ROOT','/var/www/html');"
         "require_once('/var/www/html/core/php/core.inc.php');"
         "echo config::byKey('internalAddr');\""],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode == 0 and result.stdout.strip():
        return f"http://{result.stdout.strip()}"
    return ""


def setup_api(alias: str) -> dict:
    _section("API Jeedom (optionnel)")

    detected_url = _detect_api_url(alias)
    detected_key = _detect_api_key(alias)

    if detected_url:
        _ok(f"URL détectée automatiquement : {detected_url}")
    if detected_key:
        _ok("Clé API détectée automatiquement")

    api_url = _ask("URL Jeedom", detected_url)
    api_key = detected_key or _ask_secret("Clé API (Réglages → Système → Configuration → API)")

    if api_url and api_key:
        try:
            payload = json.dumps({
                "jsonrpc": "2.0", "method": "ping",
                "params": {"apikey": api_key}, "id": 1,
            }).encode()
            req = urllib.request.Request(
                api_url.rstrip("/") + "/core/api/jeeApi.php",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                if data.get("result") == "pong":
                    _ok("API opérationnelle")
                else:
                    _err(f"Réponse API inattendue : {data}")
        except Exception as exc:
            _err(f"API inaccessible : {exc}")

    return {"api_url": api_url, "api_key": api_key}


# ── Sauvegarde ─────────────────────────────────────────────────────────────────

def save(creds: dict) -> None:
    _section("Sauvegarde")
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CREDENTIALS_PATH.open("w") as f:
        json.dump(creds, f, indent=2)
    CREDENTIALS_PATH.chmod(0o600)
    _ok(f"Credentials sauvegardés : {CREDENTIALS_PATH} (perm 600)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print(BANNER)

    if CREDENTIALS_PATH.exists():
        answer = _ask(f"Credentials existants dans {CREDENTIALS_PATH}. Reconfigurer ?", "non")
        if answer.lower() not in ("oui", "o", "yes", "y"):
            print("Configuration inchangée.")
            sys.exit(0)

    alias = setup_ssh()
    mysql_conf = setup_mysql(alias)
    api_conf = setup_api(alias)

    creds = {
        "preferred_mode": "auto",
        "ssh_alias": alias,
        **mysql_conf,
        **api_conf,
    }

    save(creds)

    print("\n── Test final ──")
    result = subprocess.run(
        ["python3", str(Path(__file__).parent / "db_query.py")],
        input='{"query": "SELECT COUNT(*) AS nb FROM eqLogic"}',
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode == 0:
        _ok(f"db_query.py opérationnel : {result.stdout.strip()}")
    else:
        _err(f"db_query.py en erreur : {result.stderr}")

    print("\n✓ Configuration terminée. La skill jeedom-audit est prête.\n")


if __name__ == "__main__":
    main()
