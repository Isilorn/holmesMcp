# PROJECT_STATE.md — État courant du projet Holmes MCP

> Mis à jour à chaque fin de session significative. Source de vérité pour la continuité entre sessions Claude Code.

---

## État général

| Champ | Valeur |
|---|---|
| **Version courante** | `v0.0.0` (J0 en cours) |
| **Jalon en cours** | J0 — Bootstrap repo + POC D2.3 |
| **Session en cours** | J0-1 terminée / J0-2 prochaine (SSH — snapshot Proxmox requis) |
| **Dernière session** | `2026-05-03-j0-1-bootstrap` |
| **Statut global** | 🟠 EN COURS — J0-1 bootstrap ✅, J0-2 SSH POC en attente snapshot Proxmox |

---

## Jalon courant : J0 (en cours)

### J0-1 ✅ Bootstrap repo (2026-05-03)

- Structure complète du plugin (PHP shell, daemon Python POC-ready, tests, CI)
- Gardes-fous : `.gitignore` strict + hooks pre-commit/pre-push (scan credentials)
- D9.1 ✅ : httpx + sqlparse + structlog + pymysql → ADR-0002 proposed
- D11.6 ✅ : ruff → ADR-0002 proposed
- D10.3 ✅ : docs/ embarqué dans main → ADR-0014 proposed
- D12.6 ✅ : MkDocs Material + docs.yml CI → ADR-0014 proposed

### J0-2 prochaine — SSH + POC daemon (snapshot Proxmox requis avant)

1. `netstat` sur box → D3.2 (port défaut)
2. Lecture `common.config.php`, test `CREATE USER` → D4bis.1 + D4bis.2
3. Install plugin shell via mécanisme Jeedom (zip + market ou SCP)
4. Démarrage daemon → vérification état vert "Démon" dans UI
5. Test `tools/list` via MCP Inspector depuis la machine Claude Code

### J0-3 prochaine — Validation Claude Desktop (matière PO)

- Hypothèse #7 : connexion Claude Desktop HTTP LAN → plan B HTTPS si échec
- ADR-0018 (résultat POC complet)

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
| D1.2 | J0 | Version spec MCP cible (dernière stable J0) | Compatibilité SDK MCP Python, support N/N-1 |
| D3.2 | J0 | Port par défaut + path `/mcp` (vérification ports plugins majeurs sur box PO) | Port haut >8000, libre des plugins majeurs |
| D4bis.1 | J0 | Driver MySQL : PyMySQL (reco) vs mysql-connector-python | Pure Python, maintenance active, MariaDB 10.x compat |
| D4bis.2 | J0 | Mécanisme création user MySQL RO à l'install (lire `common.config.php`, test `CREATE USER` privilege) | Message clair si échec privilege |
| ~~D9.1~~ | ~~J0~~ | ~~Libs Python~~ | ✅ **Tranché J0-1** : httpx + sqlparse + structlog — ADR-0002 |
| ~~D10.3~~ | ~~J0~~ | ~~docs/ embarqué vs branche~~ | ✅ **Tranché J0-1** : docs/ dans main — ADR-0014 |
| D10.8 | J0 | Vérification ID `holmesMcp` libre sur market Jeedom + collision marque | Recherche market officielle |
| ~~D11.6~~ | ~~J0~~ | ~~Lint/format Python~~ | ✅ **Tranché J0-1** : ruff — ADR-0002 |
| ~~D12.6~~ | ~~J0~~ | ~~MkDocs Material + CI docs.yml~~ | ✅ **Tranché J0-1** : MkDocs Material — ADR-0014 |
| D12.7 | J0 | Procédure soumission market : étapes manuelles vs automatisables | Vérification API/UI développeur Jeedom |
| D5.8 | J1 | Matrice couverture skill jeedom-audit WF1-WF13 ↔ tools MCP V1 | Livrable : `docs/skill-coverage-matrix.md` |
| D6.3 | J1 | Plafond énumération resources (typique 50 entités) | Claude Desktop réactif, mesure empirique box PO |
| D14.4 | J1 | UI vue dédiée logs Holmes MCP (framework JS, refresh, filtres) | Jeedom standard, sans dépendance JS exotique |
| D15.2 | J1 | Liste hard-codée plugins à filtrer (10 plugins les plus installés) | Livrable : enrichissement `_domain/sanitize.py` |
| D2.4 | J0 | Mécanisme exact isolation Python (venv Jeedom 4.4.9+ natif vs `dependance.lib` Mips) | Bénéfice clair sans complexifier le diagnostic |

---

## POC requis avant validation (🟣)

| POC | Jalon | Hypothèses à valider | Goulet PO |
|---|---|---|---|
| D2.3 — Faisabilité daemon Python sur Bookworm | J0 | 7 hypothèses (voir brief §"POCs requis") | Hypothèse #7 : validation Claude Desktop sur machine PO (HTTP non-TLS LAN) |

**Plan B si hypothèse #7 échoue** : HTTPS self-signed (génération auto `openssl` à l'install, exposition daemon en HTTPS). Coût +1 à 2 jours. ADR documentant le choix.

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
| Claude Desktop HTTP non-TLS LAN (D2.3 hypothèse #7) | 🔴 Élevé | POC J0, plan B HTTPS self-signed |
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
| ADR-0018 | Résultat POC D2.3 | *(à rédiger post-POC J0)* |
| ADR-0019 | Couverture skill jeedom-audit D5.8 | *(à rédiger post-J1)* |
