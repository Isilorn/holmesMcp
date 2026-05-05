# J7bis-2 — Audit live Holmes MCP v1.1.0 + couverture jeedom-audit

> **Session :** J7bis-2
> **Date :** 2026-05-05
> **Périmètre :** Audit live + gap analysis update post-J7bis-1
> **Playbook :** `docs/skill-migration-audit-playbook.md`
> **Destinataires :** PO Holmes MCP (clôture J7bis, brief J8)

---

## 1. Contexte

**Référence précédente :** J8-audit (2026-05-05) — gap analysis complète jeedom-audit → Holmes MCP sur v1.0.0. Résultat : 1 gap fonctionnel (WF6), 4 items d'amélioration identifiés.

**J7bis-1 (2026-05-05)** a livré les 4 items : `find_command_usages`, documentation LIMIT, auto-backtick `trigger`/`repeat`/`update`, FAQ 4.4.x. Version passée à v1.1.0 (26 tools, 686 tests unitaires).

**Objectif J7bis-2 :** valider Holmes MCP v1.1.0 en conditions réelles (168 tests d'intégration live), re-confirmer la couverture des 13 WF avec le nouvel outil, et produire la mise à jour de la gap analysis.

**Pré-requis respectés :** snapshot Proxmox pris avant session, daemon démarré via `deamon_start()` PHP (www-data), SSH alias `Jeedom` opérationnel.

---

## 2. Gap analysis — 13 WF × Holmes MCP v1.1.0

### Changements depuis J8-audit

| WF | Verdict J8-audit | Verdict J7bis-2 | Motif |
|----|-----------------|-----------------|-------|
| WF6 | ❌ Gap fonctionnel | ✅ Couvert | `find_command_usages` livré J7bis-1 |
| Tous autres | inchangé | inchangé | — |

### Tableau complet

| WF | Nom | Verdict | Outils Holmes MCP v1.1.0 | Gap résiduel |
|----|-----|---------|--------------------------|--------------|
| WF1 | Audit général | ✅ Données couvertes | `get_install_overview`, `get_health_summary`, `list_plugins`, `query_sql` | Seuils health-checks + templates rapport → restent dans la skill (gaps de connaissance) |
| WF2 | Diagnostic scénario | ✅ Complet | `describe_scenario`, `get_scenario_log`, `get_scenario_structure` | — |
| WF3 | Diagnostic équipement | ⚠️ Partiel | `get_equipment` (currentValue+collectDate via API) | Schémas plugin-spécifiques (batterie, communication) → gap de connaissance, pas fonctionnel |
| WF4 | Diagnostic plugin | ✅ Complet | `list_plugins`, `get_health_summary` | — |
| WF5 | Explication scénario | ✅ Complet | `describe_scenario` | scenario-grammar.md reste dans la skill (gap de connaissance) |
| WF6 | Graphe d'usage | ✅ Complet | `find_command_usages` (cmd→scénarios), `find_scenario_dependencies` (scenario→scenario) | — |
| WF7 | Suggestions refactor | ✅ Données couvertes | `query_sql`, outils inventaire | Anti-patterns + templates → restent dans la skill (gaps de connaissance) |
| WF8-11 | Quick reads | ✅ Mieux couvert | `get_equipment`, `get_command_history`, `get_datastore_variable`, `find_*` | — |
| WF12 | Cartographie orchestration | ✅ Complet | `get_scenario_structure(follow_scenario_calls=3)`, `find_scenario_dependencies` | Template mermaid → reste dans la skill |
| WF13 | Forensique causale | ✅ Données couvertes | `get_scenario_log`, `tail_log`, `get_command_history`, `get_health_summary`, `query_sql` | Méthodologie multi-tour → reste dans la skill |

**Verdict global v1.1.0 : 13/13 WF couverts — aucun gap fonctionnel résiduel.**

### Distinction gap fonctionnel vs gap de connaissance

| Type | WF concernés | Action |
|------|-------------|--------|
| Gap fonctionnel | aucun (WF6 résolu) | — |
| Gap de connaissance | WF1, WF3, WF5, WF7, WF12, WF13 | Logique métier reste dans SKILL.md — c'est la valeur ajoutée de la skill |

---

## 3. Macro étude de migration — mise à jour post-J7bis-1

La classification Éliminer / Transformer / Conserver est inchangée depuis J8-audit §2. Seule la section WF6 du cookbook SQL évolue.

### 3.1 Classification (inchangée)

**Éliminer (~13 composants, ~4 000 lignes)** : `setup.py`, `api_call.py`, `db_query.py`, `logs_query.py`, `scenario_tree_walker.py`, `resolve_cmd_refs.py`, `usage_graph.py`, `_common/credentials.py`, `_common/ssh.py`, `_common/router.py`, `_common/sensitive_fields.py`, `_common/version_check.py`, `references/connection.md`, `references/api-jsonrpc.md`, `references/api-http.md`.

**Transformer** : `sql-cookbook.md` (majorité supprimée), `SKILL.md` (setup → Bearer token, scripts → appels MCP).

**Conserver** : `references/health-checks.md`, `references/audit-templates.md`, `references/scenario-grammar.md`, 6 guides plugins tier-1, logique d'orchestration des 13 WF.

### 3.2 Requêtes SQL de substitution pour WF6 (mise à jour J7bis-2)

`find_command_usages(cmd_id)` couvre désormais nativement les 3 axes de WF6. Pour usage depuis SKILL.md si l'outil est jugé insuffisant, les requêtes SQL de substitution corrigées pour MariaDB sont :

```sql
-- Scénarios dont ce cmd est un trigger
SELECT id, name FROM scenario
WHERE JSON_CONTAINS(`trigger`, '"#<cmd_id>#"')
LIMIT 50

-- Expressions (conditions/actions) référençant ce cmd
-- MariaDB : JSON_SEARCH (CAST AS JSON non supporté)
SELECT DISTINCT s.id, s.name, expr.type AS expr_type, expr.expression
FROM scenarioExpression expr
JOIN scenarioSubElement ss ON expr.scenarioSubElement_id = ss.id
JOIN scenarioElement sel   ON ss.scenarioElement_id = sel.id
JOIN scenario s
  ON JSON_SEARCH(s.scenarioElement, 'one', CAST(sel.id AS CHAR)) IS NOT NULL
WHERE expr.expression LIKE '%#<cmd_id>#%'
LIMIT 50

-- Variables dataStore référençant ce cmd
SELECT `key`, value, link_id FROM dataStore
WHERE value LIKE '%#<cmd_id>#%'
LIMIT 50
```

> **Correction J7bis-2 :** La requête expressions du J8-audit utilisait `CAST(sel.id AS JSON)` — syntaxe MySQL non supportée par MariaDB (Jeedom Bookworm). Corrigée en `JSON_SEARCH(..., 'one', CAST(sel.id AS CHAR)) IS NOT NULL`. Même bug corrigé dans `find_command_usages()` (Audit A).

### 3.3 Contraintes Holmes MCP à documenter dans SKILL.md — mise à jour

| Contrainte J8-audit | Statut v1.1.0 |
|---------------------|--------------|
| LIMIT auto-injecté (50 si absent, max 200) | Inchangé — documenter dans SKILL.md |
| Backticks manuels (`trigger`, `repeat`, `update`) | **Partiellement résolu** : Holmes auto-backtick ces 3 mots depuis J7bis-1. Autres mots réservés → manuels. |
| Jeedom ≥ 4.5 uniquement | Inchangé |

---

## 4. Impacts Holmes MCP — bilan post-J7bis-1

| Impact J8-audit | Priorité | Statut v1.1.0 |
|-----------------|----------|---------------|
| A — `find_command_usages` | Moyenne | ✅ Livré J7bis-1 — bug SQL MariaDB corrigé J7bis-2 |
| B — Documentation LIMIT `query_sql` | Faible | ✅ Livré J7bis-1 (docstring + section diagnostic MkDocs) |
| C — Auto-backtick mots réservés | Faible | ✅ Livré J7bis-1 (`trigger`, `repeat`, `update`) |
| D — FAQ Jeedom 4.4.x | Faible | ✅ Livré J7bis-1 |

**Nouvel impact découvert en J7bis-2 :**

| # | Impact | Priorité | Effort | Action |
|---|--------|----------|--------|--------|
| F | SQL cookbook J8-audit : syntaxe `CAST AS JSON` invalide MariaDB | Documentaire | Trivial | ✅ Corrigé dans J8-audit §2.2 (ce commit) |

**Aucun impact bloquant pour J8.** Holmes MCP v1.1.0 est prêt pour la bêta et la migration jeedom-audit.

---

## 5. Synthèse

### Audit A — Tests d'intégration live

| Métrique | Résultat |
|----------|---------|
| Tests lancés | 168 |
| Tests passés (avant correctif) | 164 |
| Tests échoués (avant correctif) | 4 (`TestFindCommandUsagesLive`) |
| Tests passés (après correctif) | **168 / 168** |
| Tests unitaires (local) | **686 / 686** |
| Crash daemon | aucun |

**Bug identifié et corrigé :**

- **Fichier :** `resources/holmesMcpd/tools/equipments.py` ligne 466
- **Cause :** `JSON_CONTAINS(s.scenarioElement, CAST(sel.id AS JSON))` — `CAST AS JSON` est syntaxe MySQL, non supportée par MariaDB (Jeedom Bookworm)
- **Découverte connexe :** `scenario.scenarioElement` stocke les IDs comme chaînes JSON (`["502"]`) et non comme entiers (`[502]`)
- **Fix :** `JSON_SEARCH(s.scenarioElement, 'one', CAST(sel.id AS CHAR)) IS NOT NULL`
- **Impact :** 686 tests unitaires non affectés (mocks DB), 168/168 intégration ✅

### Audit E — Sanity check (5 requêtes réelles sur box PO)

| Check | Résultat |
|-------|---------|
| `get_install_overview` | ✅ Jeedom 4.5.3, 216 eq, 61 scénarios, 6214 cmds — aucun credential |
| `find_command_usages(71)` cmd non référencée | ✅ 0/0/0 — correct |
| `find_command_usages(15942)` cmd référencée | ✅ 2 triggers + 1 expression trouvés |
| `get_health_summary` | ✅ plugins_nok=[], 2 crons actifs (wifilightV2) — aucun credential |
| `query_sql` avec `trigger` (auto-backtick) | ✅ 3 lignes retournées — auto-backtick opérationnel |
| `query_sql` credentials check (eqLogic.configuration) | ✅ aucun mot sensible dans les sorties |
| `describe_scenario(74)` | ✅ 4/4 refs `#cmdId#` résolues → `#[O][E][C]#` — aucun credential |

### Pour la décision de migration J8

```
┌──────────────────────────────────────────────────────────────────┐
│  VERDICT MIGRATION jeedom-audit → Holmes MCP (v1.1.0)            │
├──────────────────────┬───────────────────────────────────────────┤
│ Faisabilité          │ ✅ Haute — 13/13 WF couverts              │
│ Effort estimé        │ Moyen — refactoring SKILL.md              │
│ Gain infrastructure  │ Élevé — ~4 000 lignes code/doc supprimées │
│ Régression           │ Nulle — WF6 désormais natif               │
│                      │ Support Jeedom 4.4.x supprimé (doc)       │
│ Prérequis            │ Holmes MCP v1.1.0 installé ✅              │
└──────────────────────┴───────────────────────────────────────────┘
```

**J7bis-2 clôturée. J7bis ✅ — aucun item bloquant pour J8.**

---

## Annexe — DoD J7bis-2

- [x] Suite intégration live exécutée — 168/168 ✅
- [x] `find_command_usages` validé live sur la box
- [x] Gap analysis 13 WF complète — verdict par WF + distinction gap fonctionnel / connaissance
- [x] Macro étude de migration complète — classification Éliminer/Transformer/Conserver
- [x] Requêtes SQL de substitution corrigées pour MariaDB (WF6 expressions)
- [x] Impacts Holmes MCP évalués — tous résolus, 1 nouveau impact documentaire traité
- [x] Document de session rédigé dans `docs/sessions/` (structure 6 sections playbook)
- [x] Playbook mis à jour (voir ci-dessous)
- [x] Zéro crash daemon pendant la session
- [x] Aucun item bloquant pour J8
