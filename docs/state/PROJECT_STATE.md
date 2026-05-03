# PROJECT_STATE.md — État courant du projet Holmes MCP

> Mis à jour à chaque fin de session significative. Source de vérité pour la continuité entre sessions Claude Code.

---

## État général

| Champ | Valeur |
|---|---|
| **Version courante** | `v0.0.0` (J1 à venir) |
| **Jalon en cours** | J1 — _core + matrice skill |
| **Session en cours** | J1 prochaine |
| **Dernière session** | `2026-05-03-j0-3-claude-desktop` |
| **Statut global** | 🟢 J0 ✅ TERMINÉ — J0-1 ✅, J0-2 ✅, J0-3 ✅ (ADR-0018 accepted, HTTP LAN retenu) |

---

## Jalon J0 ✅ Clôturé (2026-05-03)

### J0-1 ✅ Bootstrap repo + outils dev (2026-05-03)

- Structure complète du plugin (PHP shell, daemon Python POC-ready, tests, CI)
- Gardes-fous : `.gitignore` strict + hooks pre-commit/pre-push (scan credentials)
- D9.1 ✅ : httpx + sqlparse + structlog + pymysql → ADR-0002 proposed
- D11.6 ✅ : ruff → ADR-0002 proposed
- D10.3 ✅ : docs/ embarqué dans main → ADR-0014 proposed
- D12.6 ✅ : MkDocs Material + docs.yml CI → ADR-0014 proposed
- Scripts dev testés et validés : `dev/add-sudo-temp.sh` + `dev/remove-sudo-temp.sh` + `dev/secrets.cfg`

### J0-2 ✅ SSH + POC daemon (2026-05-03)

- D3.2 ✅ : port défaut **8765** (libre sur la box, aucune collision plugins)
- D4bis.1 ✅ : PyMySQL confirmé (MariaDB 10.x Bookworm, localhost)
- D4bis.2 ✅ : `CREATE USER` via `sudo mysql` (unix_socket root, user jeedom trop restrictif)
- D2.4 ✅ : venv natif Jeedom (`resources/python_venv/`) — `system::update()` Jeedom 4.4.9+
- Plugin installé sur la box, dépendances OK, daemon UP (PID confirmé, state:ok)
- `tools/list` → tool `hello` retourné via Streamable HTTP — hypothèses D2.3 #1-#6 validées
- Bugs corrigés en session : `realpath()` symlink venv, `FastMCP.run()` API 1.27.0, `list_tools()` async
- Infrastructure MySQL : user `jeedom_mcp_ro` créé, `GRANT SELECT ON jeedom.*`, mdp dans `/etc/holmes_mcp_ro.conf`

### J0-3 ✅ Validation client MCP LAN (2026-05-03)

- Hypothèse #7 ✅ validée via **Claude Code** (HTTP LAN natif, `type: "http"` dans `.mcp.json`)
- Claude Desktop : ne supporte pas HTTP LAN direct — contournement via `mcp-remote` (stdio→HTTP)
- Plan B HTTPS self-signed **abandonné** — HTTP suffisant pour V1
- ADR-0018 rédigée et accepted

### J0 ✅ Clôturé (2026-05-03)

Toutes les hypothèses D2.3 validées. Plan B HTTPS self-signed abandonné (HTTP suffisant). ADR-0018 accepted. J0-3bis annulée.

**Stratégie de test validée (ADR-0018) :** les tests d'intégration V1 sont réalisés en priorité depuis **Claude Code**. C'est Claude Code qui les exécute via SSH sur la box PO — sans intervention du PO pour les tests techniques. Le PO intervient uniquement pour les validations de matière (sanity check UI, critère D8.3 #5).

---

## Décisions tranchées (référence brief)

Toutes les décisions 🟡/🟢 du brief sont tranchées. Voir `docs/sources/00-brief-cadrage.md` §"Tableau récapitulatif des décisions". Résumé des pivots :

- **D2.1** : daemon Python 3.11+, SDK MCP officiel Anthropic
- **D2.2** : PHP enveloppe market uniquement (manifeste, hooks, UI config, callback)
- **D3.1** : Streamable HTTP (spec MCP 2025-03-26+)
- **D4.1-D4.7** : Bearer token par user Jeedom (`User->setOption()`)
- **D4bis.1-D4bis.7** : MySQL via user RO `jeedom_mcp_ro` + logs fichier + API JSON-RPC localhost ; écriture V2+ via API uniquement, jamais SQL
- **D5.1** : lecture seule V1, écriture candidate V2+
- **D5.3** : 25 tools en 6 familles dont `query_sql` restreint + `get_config` dédié
- **D5.5** : stabilité semver V1.x (schémas tools/resources stables)
- **D8.3** : 9 critères de sortie V1.0.0 (dont sanity check PO #5 et doc MkDocs #9)
- **D8.4** : bêta privée 2+ semaines sur box PO avant soumission market en bêta
- **D10.4** : AGPL-3.0 + bascule jeedom-skills MIT→AGPL conditionnée copyright holder unique
- **D10.5** : branche `main` (stable) + `develop` (intégration)
- **D11.8** : isolation totale credentials du repo (non négociable)
- **D15.1** : sanitisation 3 mécanismes cumulés (whitelist + regex + hard-code plugins) + mask + count

---

## Décisions ouvertes (🔵 — à trancher en J0/J1)

| Décision | Jalon | Question | Critères |
|---|---|---|---|
| ~~D1.2~~ | ~~J0~~ | ~~Version spec MCP cible~~ | ✅ **Tranché J1-1** : spec **2025-03-26** (Streamable HTTP) — mcp==1.27.0 |
| ~~D3.2~~ | ~~J0~~ | ~~Port par défaut~~ | ✅ **Tranché J0-2** : port **8765** (libre sur box PO) |
| ~~D4bis.1~~ | ~~J0~~ | ~~Driver MySQL~~ | ✅ **Tranché J0-2** : PyMySQL (confirmé MariaDB 10.x Bookworm) |
| ~~D4bis.2~~ | ~~J0~~ | ~~Création user MySQL RO~~ | ✅ **Tranché J0-2** : `sudo mysql` unix_socket (user jeedom sans CREATE USER global) |
| ~~D2.4~~ | ~~J0~~ | ~~Isolation Python~~ | ✅ **Tranché J0-2** : venv natif Jeedom `resources/python_venv/` |
| ~~D9.1~~ | ~~J0~~ | ~~Libs Python~~ | ✅ **Tranché J0-1** : httpx + sqlparse + structlog — ADR-0002 |
| ~~D10.3~~ | ~~J0~~ | ~~docs/ embarqué vs branche~~ | ✅ **Tranché J0-1** : docs/ dans main — ADR-0014 |
| D10.8 | J0 | Vérification ID `holmesMcp` libre sur market Jeedom + collision marque | Recherche market officielle |
| ~~D11.6~~ | ~~J0~~ | ~~Lint/format Python~~ | ✅ **Tranché J0-1** : ruff — ADR-0002 |
| ~~D12.6~~ | ~~J0~~ | ~~MkDocs Material + CI docs.yml~~ | ✅ **Tranché J0-1** : MkDocs Material — ADR-0014 |
| D12.7 | J0 | Procédure soumission market : étapes manuelles vs automatisables | Vérification API/UI développeur Jeedom |
| ~~D5.8~~ | ~~J1~~ | ~~Matrice couverture skill jeedom-audit~~ | ✅ **Tranché J1-2** : 13/13 WF couverts, 0 ajout requis — `docs/skill-coverage-matrix.md` + ADR-0019 |
| D6.3 | J1 | Plafond énumération resources (typique 50 entités) | Claude Desktop réactif, mesure empirique box PO |
| ~~D14.4~~ | ~~J1~~ | ~~UI vue dédiée logs (framework JS)~~ | ✅ **Tranché J1-1** : tableau HTML natif Jeedom + polling AJAX `setInterval` — pas de dépendance JS externe |
| ~~D15.2~~ | ~~J1~~ | ~~Liste hard-codée plugins à filtrer~~ | ✅ **Tranché J1-1** : liste produite dans `_domain/sanitize.py` — 10 plugins les plus installés (jMQTT, Aqara, Zigbee2MQTT, Sonos, Philips Hue, Z-Wave, Netatmo, ecodevices, rfxcom, agenda) |

---

## POC requis avant validation (🟣)

**D2.3 ✅ — Faisabilité daemon Python sur Bookworm** : toutes les hypothèses #1-#7 validées (J0). ADR-0018 accepted. HTTP retenu, plan B abandonné. Aucun POC ouvert.

---

## Goulets d'étranglement actifs

| Goulet | Type | Matière attendue | Jalon | Statut |
|---|---|---|---|---|
| Aucun | — | — | — | — |

*À mettre à jour si un goulet bloque une session.*

---

## Pré-requis externes

| Pré-requis | Responsable | Dépendance | Statut |
|---|---|---|---|
| Vérification copyright holder `jeedom-skills` (D10.4) | PO | J0 (avant relicence) | 🔴 À faire |
| ADR relicence `jeedom-skills` MIT→AGPL | Claude Code (sur repo jeedom-skills) | Après vérification copyright | 🔴 À faire |
| Communication forum annonce conjointe V1.0.0 | PO | J7 (co-événement release) | 🔴 Futur |

---

## Risques actifs surveillés

| Risque | Niveau | Mitigation |
|---|---|---|
| ~~Claude Desktop HTTP non-TLS LAN (D2.3 hypothèse #7)~~ | ~~🔴 Élevé~~ | ✅ Clos J0-3 — HTTP LAN natif via Claude Code, Claude Desktop via mcp-remote |
| `CREATE USER` privilege absent sur install PO (D4bis.2) | 🟡 Moyen | Message clair, détection à l'install |
| ID `holmesMcp` pris sur market (D10.8) | 🟡 Moyen | Vérification J0, alternatives préparées |
| Validateur market Jeedom (critères partiellement publics) | 🟡 Moyen | Pre-submit checklist en J0/J7 |
| Dérive de scope V1 | 🟡 Moyen | Discipline anti-drift D8.2, ROADMAP.md comme exutoire |

---

## ADRs Holmes MCP

| # | Titre | Statut |
|---|---|---|
| ADR-0001 | Architecture Holmes MCP | draft |
| ADR-0002 | Stack technologique | proposed |
| ADR-0003 | Version spec MCP cible V1 | draft |
| ADR-0004 | Authentification MCP externe | draft |
| ADR-0005 | Canaux d'accès aux données Jeedom | draft |
| ADR-0006 | Périmètre fonctionnel V1 | draft |
| ADR-0007 | Liste des 25 tools V1 | draft |
| ADR-0008 | Liste des 5 resources V1 | draft |
| ADR-0009 | Réutilisation scripts jeedom-audit | draft |
| ADR-0010 | Nom et identité produit | draft |
| ADR-0011 | Licence AGPL-3.0 | draft |
| ADR-0012 | Stratégie de tests | draft |
| ADR-0013 | Sécurité opérationnelle — credentials | draft |
| ADR-0014 | Distribution market et versioning | proposed |
| ADR-0015 | Modèle opérationnel PO / Claude Code | draft |
| ADR-0016 | Observabilité | draft |
| ADR-0017 | Sanitisation et guardrails | draft |
| ADR-0018 | Résultat POC D2.3 | accepted |
| ADR-0019 | Couverture skill jeedom-audit D5.8 | accepted |
