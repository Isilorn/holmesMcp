# CLAUDE.md — Holmes MCP

Plugin Jeedom natif (AGPL-3.0) exposant la box comme **serveur MCP en lecture seule**.
Enveloppe PHP (`core/`, `desktop/`) + daemon Python (`resources/holmesMcpd/`).
Binôme : le PO décide et fournit les matières physiques, Claude Code code, rédige et exécute.

---

## Ce qui fait foi

| Document | Statut |
|---|---|
| `docs/sources/00-brief-cadrage.md` | **Source d'autorité figée.** Ne se modifie jamais — tout amendement passe par une ADR |
| `docs/decisions/ADR-*.md` | Décisions d'architecture. Une décision non écrite ici n'existe pas |
| `docs/PLANNING.md` | Plan vivant : jalons, DoD |
| `docs/state/PROJECT_STATE.md` | **État courant** — doit correspondre au dernier commit |

## Ce qui ne fait PAS foi

- `docs/sessions/` — **journaux datés**. De l'histoire, pas des instructions. On ne les réécrit
  pas quand une procédure change : on date le fait devenu faux.
- `site/` — généré par MkDocs. Ne jamais éditer à la main.

---

## Interdits durs

1. **Lecture seule absolue en V1.** La garantie est au niveau base (`jeedom_mcp_ro`, `GRANT
   SELECT`), pas au niveau du code. L'écriture est candidate V2+ et passera par l'API JSON-RPC,
   **jamais par SQL**.
2. **Aucun `kill`, `pkill`, ni signal sur la box** — y compris sur un process lancé par Claude
   Code — **sans autorisation explicite du PO dans le chat**. Incidents J6-1 et J7-2.
3. **Snapshot Proxmox avant toute session live.** L'incident J6-1 a coûté les données de
   géofencing et de présence.
4. **Aucune copie de secret.** Chemin canonique unique :
   `source "${FLEET_SECRETS:-$HOME/.config/fleet/secrets.env}"`. Un secret absent de ce fichier :
   **s'arrêter et le demander**, ne jamais en créer ni en coder en dur. Ne jamais afficher une
   valeur — comparer par `sha256sum`.
5. **Le sudo appartient à `Servers-setup`.** On appelle les scripts à leur chemin, on n'en fait
   pas de copie : `Servers-setup/scripts/add-sudo-temp.sh Jeedom` — **hôte toujours nommé** (sans
   argument : toute la flotte), retrait **obligatoire** même en cas d'échec (dérive horaire à
   `:15`). Pour une commande ponctuelle, mode par défaut : mot de passe pipé, rien de posé.
6. **IPs d'exemple en RFC-5737** (`203.0.113.x`) — y compris en Markdown. Le hook pre-push bloque
   toute IP privée.
7. **Jamais de `curl`/`httpx` pour un smoke test MCP** — c'est ce qui déclenchait le spin
   CLOSE-WAIT. Utiliser `build_mcp()` ou `tests/smoke/smoke_mcp_clean.py`.
8. **Clean room.** Conception à partir des seuls scripts `jeedom-audit`, de la doc Jeedom
   officielle et de la spec MCP. On n'audite pas le code des autres plugins MCP Jeedom.
9. **Couverture 100 % sur `_domain/sanitize.py`** — non négociable. C'est le cœur de la confiance
   produit.

---

## Le piège de sécurité de ce dépôt

Il est **public**. Deux conséquences vérifiées le 2026-09-08 :

- **Ce qui l'a protégé pendant 4 mois est une ligne de `.gitignore`, pas le hook.** Un garde-fou
  de pre-commit lit le **diff stagé** — il ne protège **jamais** l'historique.
- **`.routines.conf` est impératif ici** : sans lui, `mem-snapshot` retombe sur son défaut
  `pilotage/archives/` *dans* le dépôt et publierait des fiches décrivant la doctrine sudo de la
  flotte et les chemins de la box. Les archives vont dans `../Archives` (GitHub **privé**).

⚠️ Dans une commande inline, `grep` est une **fonction shell** qui respecte les `.gitignore` —
donc aveugle sur un fichier de secrets. Préfixer par `command` ou le chemin absolu dès que le
résultat compte : `/usr/bin/grep`, `command jq`.

---

## Contrôles

```bash
ruff check resources/holmesMcpd/ tests/ && ruff format --check resources/holmesMcpd/ tests/
python3 -m pytest tests/unit/ -q                      # 722 tests, < 2 s
python3 -m pytest tests/integration/ -q               # live sur la box, snapshot requis
~/.claude/skills/project-conformity/scripts/project-doctor --profond
```

La CI enchaîne `lint` **puis** `unit` (`needs: lint`) : un formatage non passé débranche
silencieusement toute la suite de tests. Vérifier les deux avant de pousser.
